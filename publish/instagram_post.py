from datetime import datetime
import requests, os, sys, json, logging
from time import sleep
from urllib.parse import quote
from html import unescape
from pathlib import Path

# Has to be installed
import aiohttp, asyncio

this_path = Path(__file__).parent.resolve()
sys.path.insert(0, os.path.dirname(this_path))

from . import imgur_upload as iu
from db_access import DB
# import db_access as db

def create_caption(description, tags, comment, reddit_user, subreddit):
    caption = f"{comment}\n.\n{description}\n.\n.\nPost of u/{reddit_user} from r/{subreddit}\n.\n.\n.\n.\n.\nTags:\n{tags}"

    return quote(unescape(caption))

# Create a container for a single post (image or video)
async def create_single_item_container(user, ig_id, access_token, media_url, media_type, caption):
    if media_type == "image":
        url = f"https://graph.facebook.com/v14.0/{ig_id}/media?image_url={media_url}&caption={caption}&access_token={access_token}"
    elif media_type == "video":
        url = f"https://graph.facebook.com/v14.0/{ig_id}/media?media_type=VIDEO&video_url={media_url}&caption={caption}&access_token={access_token}"

    logging.info(f"{user}: Instagram API call with url {url}")

    async with aiohttp.request("POST", url) as resp:

        logging.info(f"{user}: Got http code: {resp.status}")

        if resp.status == 400:
            info_error = await resp.json()
            logging.error(f"{user}: Got error publishing container with info \n{info_error}\n")
            raise info_error

        ig_container = await resp.json()

        return ig_container['id']

# Create a container for a carousel item
async def create_carousel_item_container(user, ig_id, access_token, media_url, media_type):
    if media_type == "image":
        url = f"https://graph.facebook.com/v14.0/{ig_id}/media?image_url={media_url}&is_carousel_item=true&access_token={access_token}"
    elif media_type == "video":
        url = f"https://graph.facebook.com/v14.0/{ig_id}/media?media_type=VIDEO&video_url={media_url}&is_carousel_item=true&access_token={access_token}"

    logging.info(f"{user}: Instagram API call with url {url}")

    async with aiohttp.request("POST", url) as resp:
        logging.info(f"{user}: Got http code: {resp.status}")

        if resp.status == 400:
            info_error = await resp.json()
            logging.error(f"{user}: Got error publishing container with info \n{info_error}\n")
            raise info_error

        ig_container = await resp.json()

        return ig_container['id']

# Create a container for a carousel
async def create_carousel_container(user, ig_id, access_token, caption, children):
    children_query = "%2C".join(children)

    url = f"https://graph.facebook.com/v14.0/{ig_id}/media?caption={caption}&media_type=CAROUSEL&children={children_query}&access_token={access_token}"

    logging.info(f"{user}: Instagram API call with url {url}")

    async with aiohttp.request("POST", url) as resp:
        logging.info(f"{user}: Got http code: {resp.status}")

        if resp.status == 400:
            info_error = await resp.json()
            logging.error(f"{user}: Got error publishing container with info \n{info_error}\n")
            raise info_error

        ig_container = await resp.json()

        return ig_container['id']

async def publish_container(user, ig_container, ig_id, access_token):
    url = f"https://graph.facebook.com/v14.0/{ig_id}/media_publish?creation_id={ig_container}&access_token={access_token}"

    logging.info(f"{user}: Instagram API call with url {url}")

    while True:
        async with aiohttp.request("POST", url) as resp:

            logging.info(f"{user}: Got http code: {resp.status}")

            if resp.status == 400:
                info_error = await resp.json()
                if info_error['error']['code'] == 9007:
                    sleep(5)
                else:
                    logging.error(f"{user}: Got error publishing container with info \n{info_error}\n")
                    raise info_error
            else:
                info = await resp.json()

                return info['id']

async def get_url(user, post_id, access_token):
    url = f"https://graph.facebook.com/v14.0/{post_id}?fields=permalink&access_token={access_token}"

    logging.info(f"{user}: Instagram API call with url {url}")

    async with aiohttp.request("GET", url) as resp:
        logging.info(f"{user}: Got http code: {resp.status}")

        post_url = await resp.json()

        return post_url['permalink']

def get_user_data(user):
    with open(Path(f"{this_path}/../.users.json"), "r") as json_file:
        json_load = json.load(json_file)

    return {'ig_id': json_load['users'][user]['instagram_tokens']['insta_id'], 'access_token': json_load['users'][user]['instagram_tokens']['insta_token'], 'description': json_load['users'][user]['description'], 'tags': json_load['users'][user]['tags']}

# This is the main function for single posts
def post(user, file_name, file_type, comment, reddit_user, subreddit):

    db = DB(user)

    user_data = get_user_data(user)
    ig_id, access_token, description, tags = user_data['ig_id'], user_data['access_token'], user_data['description'], user_data['tags']

    # This will return a code, if it's some error the funcition will return it and won't try to post
    imgur_result = asyncio.run(iu.main(user, file_name, file_type[:5]))

    if imgur_result in (429, 400):
        return imgur_result

    # If the imgur uploading process went fine, then, continue with the posting process
    image_url = db.postGetImgurUrl(file_name)
    caption = create_caption(description, tags, comment, reddit_user, subreddit)

    try:
        ig_container = asyncio.run(create_single_item_container(user, ig_id, access_token, image_url, file_type[:5], caption))
        post_id = asyncio.run(publish_container(user, ig_container, ig_id, access_token))
    except Exception:
        return 400

    instagram_url = asyncio.run(get_url(user, post_id, access_token))

    db.postOnInstagram(file_name, "Published", instagram_url, str(datetime.now()), post_id)
    logging.info(f"{user}: Finished process of publishing single post {file_name} with url {instagram_url}")

# This is the main function for carousel posts
def post_carousel(user, posts_data, comment, reddit_user, subreddit):

    db = DB(user)

    user_data = get_user_data(user)
    ig_id, access_token, description, tags = user_data['ig_id'], user_data['access_token'], user_data['description'], user_data['tags']

    ig_containers = []

    try:
        for post in posts_data:
            file_name = post[0]
            file_type = post[1]

            imgur_result = asyncio.run(iu.main(user, file_name, file_type[:5]))

            if imgur_result == 400:
                continue
            elif imgur_result == 429:
                return 429

            image_url = db.postGetImgurUrl(file_name)

            ig_containers.append(asyncio.run(create_carousel_item_container(user, ig_id, access_token, image_url, file_type[:5])))

        if not ig_containers:
            return 400

        caption = create_caption(description, tags, comment, reddit_user, subreddit)

        ig_carousel_container = asyncio.run(create_carousel_container(user, ig_id, access_token, caption, ig_containers))
        post_id = asyncio.run(publish_container(user, ig_carousel_container, ig_id, access_token))
    except Exception:
        return 400

    instagram_url = asyncio.run(get_url(user, post_id, access_token))

    db.postCarouselOnInstagram(file_name, "Published", instagram_url, str(datetime.now()), post_id)
    logging.info(f"{user}: Finished process of publishing carousel {[x[0] for x in posts_data]} with url {instagram_url}")