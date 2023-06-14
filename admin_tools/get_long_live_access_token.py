import requests, os, sys, json, logging
from pathlib import Path

# Has to be installed
import aiohttp, asyncio

this_path = Path(__file__).parent.resolve()
sys.path.insert(0, os.path.dirname(this_path))

def get_data_users(user):
    with open(Path(f"{this_path}/../.users.json"), "r") as json_file:
        json_load = json.load(json_file)

    return {
        'app_id' : json_load['users'][user]['instagram_tokens']['id_api_insta'],
        'app_secret' : json_load['users'][user]['instagram_tokens']['id_secret_api_insta'],
        'access_token' : json_load['users'][user]['instagram_tokens']['insta_token'],
    }

# Main function - Get Long Live Access Token (For 2 months)
async def get_LLAT(user):
    logging.info(f"{user}: Started process of getting new LLAT")

    credentials = get_data_users(user)

    app_id, app_secret, access_token = credentials['app_id'], credentials['app_secret'], credentials['access_token']

    url = f"https://graph.facebook.com/v14.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={access_token}"

    try:
        async with aiohttp.request("POST", url) as resp:
            info = await resp.json()
            with open(Path(f"{this_path}/../.users.json"), "r+") as json_file:
                data = json.load(json_file)
                data['users'][user]['instagram_tokens']['insta_token'] = info['access_token']

                json_file.seek(0)
                json.dump(data, json_file)
                json_file.truncate()

            logging.info(f"{user}: Changed LLAT from ...{access_token[-5:]} to ...{info['access_token'][-5:]}")
    except Exception as e:
        logging.error(f'{user}: Got error "{e}"')
    else:
        logging.info(f"{user}: Finished process of getting new LLAT with STATUS CODE 200")