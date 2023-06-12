import requests, os, sys, json, logging
from pathlib import Path

# Has to be installed
import aiohttp, asyncio

this_path = Path(__file__).parent.resolve()
sys.path.insert(0, os.path.dirname(this_path))

def get_data_users(user):
    with open(Path(f"{this_path}/../.users.json"), "r") as json_file:
        json_load = json.load(json_file)

    return json_load['users'][user]['instagram_tokens']['insta_token']

# Main function - Get Long Live Access Token (For 2 months)
async def get_id(user):

    access_token = get_data_users(user)

    url = f"https://graph.facebook.com/v14.0/me/accounts?access_token={access_token}"

    try:
        async with aiohttp.request("GET", url) as resp:
            info = await resp.json()

            page_id = info['data'][0]['id']


        url = f"https://graph.facebook.com/v14.0/{page_id}?fields=instagram_business_account&access_token={access_token}"

        async with aiohttp.request("GET", url) as resp:
            info = await resp.json()

            with open(Path(f"{this_path}/../.users.json"), "r+") as json_file:
                data = json.load(json_file)
                data['users'][user]['instagram_tokens']['insta_id'] = info['instagram_business_account']['id']

                json_file.seek(0)
                json.dump(data, json_file)
                json_file.truncate()

                logging.info(f"{user}: Got instagram ID ended in {info['instagram_business_account']['id'][-5:]}")
    except Exception as e:
        logging.error(f'{user}: Got error "{e}"')
    else:
        logging.info(f"{user}: Finished process of getting new LLAT with STATUS CODE 200")