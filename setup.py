import os, logging
from datetime import datetime
from pathlib import Path

import asyncio
from dotenv import load_dotenv

this_path = Path(__file__).parent.resolve()

from admin_tools import get_long_live_access_token as gt
from admin_tools import get_insta_id as gi


def get_LLAT(user):
    asyncio.run(gt.get_LLAT(user))

def get_insta_id(user):
    asyncio.run(gi.get_id(user))

logging.basicConfig(filename=Path(f'{this_path}/logs/{datetime.now().date()}.log'), encoding='utf-8', level=logging.INFO, format='([%(levelname)s]:%(asctime)s.%(msecs)03d) %(message)s', datefmt='%Y/%m/%d-%H:%M:%S')


load_dotenv(Path(f"{this_path}/.env"))

# If there are multiple users
if "," in os.getenv("WORKING_USER"):
    WORKING_USER = os.getenv("WORKING_USER").split(",")

    for user in WORKING_USER:
        get_LLAT(user)
        get_insta_id(user)

# If there is only one user
else:
    WORKING_USER = os.getenv("WORKING_USER")
    get_LLAT(WORKING_USER)
    get_insta_id(WORKING_USER)