import os, sys, json, logging
from time import sleep
from pathlib import Path

# Has to be installed
import aiohttp, asyncio

this_path = Path(__file__).parent.resolve()
sys.path.insert(0, os.path.dirname(this_path))

from db_access import DB
# import db_access as db

# Function that upload an image or video
async def upload_media(user, url, client_id, media_name, media_type):

    db = DB(user)

    data = {
        media_type : open(Path(f'{this_path}/posts/{user}/{media_name}'), 'rb'),
        'type': 'file',
        'name' : media_name
    }

    headers = {
        'Authorization': f'Client-ID {client_id}'
    }

    async with aiohttp.request("post", url, data=data, headers=headers) as resp:

        http_code = resp.status

        if http_code == 200:
            try:
                info = await resp.json()
                link = info['data']['link']
                db.postAddedImgur(media_name, "uploaded", link)
                logging.info(f"{user}: Uploaded post {media_name} on imgur with url {url}")
                return 200
            except Exception:
                info = resp.text
                logging.error(f"{user}: Got error tring to encode the json response:\n{info}\n")
                return 400
        elif http_code == 429:
            logging.error(f"{user}: Imgur got {http_code} error code with response\n{resp}\n")
            return 429
        elif http_code == 502:
            sleep(10)
            asyincio.run(upload_media(user, url, client_id, media_name, media_type))
        else:
            logging.error(f"{user}: Imgur got {http_code} error code with response\n{resp}\n")
            return 400

def get_client_id(user):
    with open(Path(f"{this_path}/../.users.json"), "r") as json_file:
        json_load = json.load(json_file)

    return json_load['users'][user]['imgur_tokens']['id_api_imgur']

# Main function
async def main(user, media_name, media_type):
    url = "https://api.imgur.com/3/upload"

    client_id = get_client_id(user)

    return await upload_media(user, url, client_id, media_name, media_type)