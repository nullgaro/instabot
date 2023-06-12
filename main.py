import os, json, logging
from datetime import datetime
from time import sleep, time
from dotenv import load_dotenv
from pathlib import Path

# Have to be installed
import asyncio
from pytz import timezone
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Internal imports
this_path = Path(__file__).parent.resolve()

from admin_tools import get_long_live_access_token as gt
from db_access import DB
from publish import reddit_scrap as rs
from publish import instagram_post as ip

# Check if the whole folder structure it's correctly deployed, if not, fix it

def onstart_checks(user):

    if not os.path.exists(Path(f"{this_path}/logs")):
        os.mkdir(Path(f"{this_path}/logs"))

    two_monthly_get_LLAT(user)

    if not os.path.exists(Path(f"{this_path}/publish/posts/{user}")):
        os.mkdir(f"{this_path}/publish/posts/{user}")

    if not db[user].checkIfHaveAnyPostStageFiltered("Scrapped"):
        daily_scrap(user)


# Scheduler config

job_defaults = {
    'coalesce': False,
    'max_instances': 5
}

sched = BlockingScheduler(job_defaults=job_defaults, timezone=timezone('CET'))


# Srapping functions

def get_user_subreddits(user):
    with open(Path(f"{this_path}/.users.json"), "r") as json_file:
        json_load = json.load(json_file)

    subreddits = json_load['users'][user]['subreddits']
    return subreddits

def daily_scrap(user):
    l_single_posts_count = l_carousel_count = l_videos_count = l_failed_count = 0

    subreddits = get_user_subreddits(user)

    logging.info(f"{user}: Started process of scrapping from subreddits {subreddits}")

    for subreddit in subreddits:
        l_w, l_x, l_y, l_z = rs.scrapRedditPost(user, subreddit, 100)

        l_single_posts_count += l_w
        l_carousel_count += l_x
        l_videos_count += l_y
        l_failed_count += l_z

    logging.info(f"{user}: Finished process with {l_single_posts_count} single posts, {l_carousel_count} carousel posts and {l_videos_count} videos with {l_failed_count} failed posts in total")


# Get LLAC functions

def two_monthly_get_LLAT(user):
    asyncio.run(gt.get_LLAT(user))


# Upload post functions

def hourly_post(user, PRIORIZE_TODAYS_POSTS):
    logging.info(f"{user}: Started process of publishing a post")
    result = db[user].getOnePostStageFiltered("Scrapped", PRIORIZE_TODAYS_POSTS)
    file_name = result[0]

    if db[user].isCarousel(file_name):
        posts_data = db[user].getPostsStageFilteredCarousel(file_name, "Scrapped")
        logging.info(f"{user}: Trying to publish carousel post with posts: [{[x[0] for x in posts_data]}]")

        posting_result = ip.post_carousel(user, posts_data, result[2], result[3], result[4])

        if posting_result == 429:
            logging.error(f"{user}: Got 429, pausing posting 90_000 seconds / 25 hours")

            if "," in os.getenv("WORKING_USER"):
                jobs[f"{user}_post"].pause()
                sleep(90_000)
                jobs[f"{user}_post"].resume()
            else:
                job_post.pause()
                sleep(90_000)
                job_post.resume()

        elif posting_result == 400:
            db[user].postUpdateStage(file_name, "Invalid")
            logging.error(f"{user}: Failed posting carousel of {file_name}, trying again with other post.")
            sleep(5)
            hourly_post(user, PRIORIZE_TODAYS_POSTS)
    else:
        logging.info(f"{user}: Trying to publish post {file_name}")

        posting_result = ip.post(user, file_name, result[1], result[2], result[3], result[4])

        if posting_result == 429:
            logging.error(f"{user}: Got 429, pausing posting 90_000 seconds / 25 hours")

            if "," in os.getenv("WORKING_USER"):
                jobs[f"{user}_post"].pause()
                sleep(90_000)
                jobs[f"{user}_post"].resume()
            else:
                job_post.pause()
                sleep(90_000)
                job_post.resume()

        elif posting_result == 400:
            db[user].postUpdateStage(file_name, "Invalid")
            logging.error(f"{user}: Failed posting {file_name}, trying again with other post.")
            sleep(5)
            hourly_post(user, PRIORIZE_TODAYS_POSTS)

def set_logging_config():
    logging.basicConfig(filename=Path(f'{this_path}/logs/{datetime.now().date()}.log'), encoding='utf-8', level=logging.INFO, format='([%(levelname)s]:%(asctime)s.%(msecs)03d) %(message)s', datefmt='%Y/%m/%d-%H:%M:%S')

if __name__ == "__main__":
    # Logging config
    set_logging_config()

    # MAIN SECTION - Get the user or users that will upload a post
    load_dotenv(Path(f"{this_path}/.env"))

    PRIORIZE_TODAYS_POSTS = os.getenv("PRIORIZE_TODAYS_POSTS")
    CRONTAB_POST = os.getenv("CRONTAB_POST")
    CRONTAB_SCRAP = os.getenv("CRONTAB_SCRAP")
    CRONTAB_LLAT = os.getenv("CRONTAB_LLAT")
    JITTER = int(os.getenv("JITTER"))

    db = {}

    # If there are multiple users
    if "," in os.getenv("WORKING_USER"):
        WORKING_USER = os.getenv("WORKING_USER").split(",")


        jobs = {}

        for user in WORKING_USER:
            db[user] = DB(user)
            onstart_checks(user)

            # Here are the scheduler jobs added
            jobs[f"{user}_scrap"] = sched.add_job(daily_scrap, CronTrigger.from_crontab(CRONTAB_SCRAP), jitter=JITTER, args=[user])
            jobs[f"{user}_LLAT"] = sched.add_job(two_monthly_get_LLAT, CronTrigger.from_crontab(CRONTAB_LLAT), jitter=JITTER, args=[user])
            jobs[f"{user}_post"] = sched.add_job(hourly_post, CronTrigger.from_crontab(CRONTAB_POST), jitter=JITTER, args=[user, PRIORIZE_TODAYS_POSTS])

    # If there is only one user
    else:
        WORKING_USER = os.getenv("WORKING_USER")

        db[WORKING_USER] = DB(WORKING_USER)

        onstart_checks([WORKING_USER])

        # Here are the scheduler jobs added
        job_scrap = sched.add_job(daily_scrap, CronTrigger.from_crontab(CRONTAB_SCRAP), jitter=JITTER, args=[WORKING_USER])
        job_LLAT = sched.add_job(two_monthly_get_LLAT, CronTrigger.from_crontab(CRONTAB_LLAT), jitter=JITTER, args=[WORKING_USER])
        job_post = sched.add_job(hourly_post, CronTrigger.from_crontab(CRONTAB_POST), jitter=JITTER, args=[WORKING_USER, PRIORIZE_TODAYS_POSTS])

    logfile_update = sched.add_job(set_logging_config, CronTrigger.from_crontab("0 0 * * *"), jitter=JITTER)

    # This will start all the scheduled jobs cycle.
    sched.start()