import requests, os, sys, time, logging
from pathlib import Path

from moviepy.editor import VideoFileClip as vf
import moviepy.editor as mpe

this_path = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(this_path))

from db_access import DB

# Give the url and say the type (image or video) and download the content
def download_media(user, media_url, type, numberFile):
    media_data = requests.get(media_url).content
    if type == "jpg":
        with open(Path(f"{this_path}/posts/{user}/{numberFile}-image.jpg"), 'wb') as handler:
            handler.write(media_data)
    elif type == "mp4-audio":
        with open(Path(f"{this_path}/posts/{user}/{numberFile}-audio.mp4"), 'wb') as handler:
            handler.write(media_data)
    elif type == "mp4-video":
        with open(Path(f"{this_path}/posts/{user}/{numberFile}-video-noaudio.mp4"), 'wb') as handler:
            handler.write(media_data)

# Function to combine the audio with the image to create the video
def combine_audio(vidname, audname, outname, fps=30):
    my_clip = mpe.VideoFileClip(str(vidname))
    audio_background = mpe.AudioFileClip(str(audname))
    final_clip = my_clip.set_audio(audio_background)
    final_clip.write_videofile(str(outname),fps=fps, verbose=False, logger=None)

# Function to check height, width, duration, aspect relation -> width:height
def validatePostSpecs(height, width, duration):
    # Duration == 0 means that it's a photo
    if duration == 0:
        # Aspect relation has to be between 0.8 and 1.91 when width/height
        return round((width/height), 2) > 0.8 and round((width/height), 2) < 1.91

    # It's a video
    else:
        return width < 1920 and round((width/height), 2) > 0.8 and round((width/height), 2) < 1.77 and duration > 4 and duration < 59

# Main function
def scrapRedditPost(user, subreddit, limit):

    db = DB(user)

    l_single_posts_count = 0
    l_carousel_count = 0
    l_videos_count = 0
    l_failed_count = 0

    # CONSTS
    MAX_IMAGE_SIZE = 8388608
    MAX_VIDEO_SIZE = 104857600

    url = f"https://api.reddit.com/r/{subreddit}?limit={limit}"
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; PPC Mac OS X 10_8_7 rv:5.0; en-US) AppleWebKit/533.31.5 (KHTML, like Gecko) Version/4.0 Safari/533.31.5'}

    response = requests.request("GET", url, headers=headers)
    data = response.json()
    posts = data["data"]["children"]

    i = db.getLastPostNumber()
    # If i its NoneType means that the table it's empty so asign the first possible value if not, set the next value
    if  i is None:
        i = 1
    else:
        i += 1

    for post in posts[2:]:

        # Try do the post scrap
        try:
            video = post["data"]["is_video"]

            # If it's a gallery
            if "gallery_data" in post["data"]:
                carousel_child_counter = 0
                for photo in post["data"]["media_metadata"]:
                    if post["data"]["media_metadata"][photo]["status"] == "failed":
                        continue

                    # Delete all "amp;" because forbidden
                    media_url = post["data"]["media_metadata"][photo]["s"]["u"].replace("amp;", "")
                    height = post["data"]["media_metadata"][photo]["s"]["y"]
                    width = post["data"]["media_metadata"][photo]["s"]["x"]

                    if validatePostSpecs(height, width, 0):
                        continue

                    # If not means something worng so dont download the media
                    if not (".jpg" in media_url or ".jpeg" in media_url or ".png" in media_url):
                        continue

                    # Checks if it's on the database
                    if not (db.getMachedPostUrls(media_url) == 0):
                        # Delete image
                        if os.path.exists(image_name):
                            os.remove(image_name)
                        continue

                    download_media(user, media_url, "jpg", i)

                    image_name = Path(f"{this_path}/posts/{user}/{i}-image.jpg")

                    # Controls that the media is smaller than the maximum
                    if not (os.path.getsize(image_name) < MAX_IMAGE_SIZE):
                        continue

                    # Get the info for the database and control the single quotes ' for SQL
                    file_name = f"{i}-image.jpg"
                    media_type = "image"
                    id_post = post["data"]["id"]
                    reddit_user = post["data"]["author"].replace("'", "''")
                    original_post = f'reddit.com{post["data"]["permalink"]}'.replace("'", "''")
                    upvotes = post["data"]["ups"]
                    comment = post["data"]["title"].replace("'", "''")
                    epoch_time = post["data"]["created_utc"]
                    original_date = time.strftime('%d/%m/%Y', time.localtime(epoch_time))

                    db.postsInsertOneRow(file_name, media_url, media_type, id_post, reddit_user, subreddit, original_post, upvotes, comment, original_date)

                    i += 1
                    l_carousel_count += 1

                    carousel_child_counter += 1
                    if carousel_child_counter >= 10:
                        break

            else:
                # If it's a single image
                if(not video and post["data"]["thumbnail"] != "self"):
                    if not (("url_overridden_by_dest" in post["data"]) and ("preview" in post["data"])):
                        continue

                    media_url = post["data"]["url_overridden_by_dest"]
                    height = post["data"]["preview"]["images"][0]["source"]["height"]
                    width = post["data"]["preview"]["images"][0]["source"]["width"]

                    if not validatePostSpecs(height, width, 0):
                        continue

                    # If not means something worng so dont download the media
                    if not (".jpg" in media_url or ".jpeg" in media_url or ".png" in media_url):
                        continue

                    # Checks if it's on the database
                    if not (db.getMachedPostUrls(media_url) == 0):
                        continue

                    download_media(user, media_url, "jpg", i)

                    image_name = Path(f"{this_path}/posts/{user}/{i}-image.jpg")

                    if not (os.path.getsize(image_name) < MAX_IMAGE_SIZE):
                        # Delete image
                        if os.path.exists(image_name):
                            os.remove(image_name)
                        continue

                    # Get the info for the database and control the single quotes ' for SQL
                    file_name = f"{i}-image.jpg"
                    media_type = "image"
                    id_post = post["data"]["id"]
                    reddit_user = post["data"]["author"].replace("'", "''")
                    original_post = f'reddit.com{post["data"]["permalink"]}'.replace("'", "''")
                    upvotes = post["data"]["ups"]
                    comment = post["data"]["title"].replace("'", "''")
                    epoch_time = post["data"]["created_utc"]
                    original_date = time.strftime('%d/%m/%Y', time.localtime(epoch_time))

                    db.postsInsertOneRow(file_name, media_url, media_type, id_post, reddit_user, subreddit, original_post, upvotes, comment, original_date)

                    i += 1
                    l_single_posts_count += 1

                # If it's a single video
                if(video):
                    media_url = post["data"]["media"]["reddit_video"]["fallback_url"]
                    height = post["data"]["media"]["reddit_video"]["height"]
                    width = post["data"]["media"]["reddit_video"]["width"]
                    duration = post["data"]["media"]["reddit_video"]["duration"]

                    audio_url = media_url.replace(str(height), "audio")

                    if not validatePostSpecs(height, width, duration):
                        continue

                    # If not means something worng so dont download the media
                    if not (".mp4" in media_url):
                        continue

                    # Checks if it's on the database
                    if not (db.getMachedPostUrls(media_url) == 0):
                        continue

                    download_media(user, media_url, "mp4-video", i)

                    temp_video_name = Path(f"{this_path}/posts/{user}/{i}-video-not-edited.mp4")
                    video_noaudio_name = Path(f"{this_path}/posts/{user}/{i}-video-noaudio.mp4")

                    # Checks if the video has audio
                    if requests.get(audio_url).status_code != 403:
                        download_media(user, audio_url, "mp4-audio", i)
                        audio_name = Path(f"{this_path}/posts/{user}/{i}-audio.mp4")

                        combine_audio(video_noaudio_name, audio_name, temp_video_name)
                        media_type = "video_audio"

                        # Delete the only audio and only video
                        os.remove(video_noaudio_name)
                        os.remove(audio_name)

                    # If has not audio, save the video only
                    else:
                        os.rename(video_noaudio_name, temp_video_name)
                        media_type = "video_noaudio"

                    # Check if the video is bigger than de maximum allowed and it's between the maximum and minimum time allowd
                    if not (os.path.getsize(temp_video_name) < MAX_VIDEO_SIZE):
                        # Delete video
                        if os.path.exists(temp_video_name):
                            os.remove(temp_video_name)
                        continue

                    # ffmpeg installed through pacman
                    os.system(f"ffmpeg -nostdin -loglevel error -i {temp_video_name} -c:v libx264 -profile:v main -level:v 3.0 -x264-params scenecut=0:open_gop=0:min-keyint=72:keyint=72:ref=4 -c:a aac -crf 23 -maxrate 3500k -bufsize 3500k -ar 44100 -b:a 128k -sn -f mp4 {Path(f'{this_path}/posts/{user}/{i}-video.mp4')}")
                    os.remove(temp_video_name)

                    # Get the info for the database and control the single quotes ' for SQL
                    file_name = f"{i}-video.mp4"
                    id_post = post["data"]["id"]
                    reddit_user = post["data"]["author"].replace("'", "''")
                    original_post = f'reddit.com{post["data"]["permalink"]}'.replace("'", "''")
                    upvotes = post["data"]["ups"]
                    comment = post["data"]["title"].replace("'", "''")
                    epoch_time = post["data"]["created_utc"]
                    original_date = time.strftime('%d/%m/%Y', time.localtime(epoch_time))

                    db.postsInsertOneRow(file_name, media_url, media_type, id_post, reddit_user, subreddit, original_post, upvotes, comment, original_date)

                    i += 1
                    l_videos_count += 1

        # If failed, don't worry, don't save it and just don't stop
        except Exception as e:
            l_failed_count += 1

            # Delete audio of video if exists
            if os.path.exists(Path(f"{this_path}/posts/{user}/{i}-audio.mp4")):
                os.remove(Path(f"{this_path}/posts/{user}/{i}-audio.mp4"))

            # Delete image of video if exists
            if os.path.exists(Path(f"{this_path}/posts/{user}/{i}-video-noaudio.mp4")):
                os.remove(Path(f"{this_path}/posts/{user}/{i}-video-noaudio.mp4"))

            # Delete video if exists
            if os.path.exists(Path(f"{this_path}/posts/{user}/{i}-video.mp4")):
                os.remove(Path(f"{this_path}/posts/{user}/{i}-video.mp4"))
        finally:
            # Delete temp files if exists (Second try) -- It has to be done out of the exception because some errors
            if os.path.exists(Path(f"{this_path}/../../{i}-videoTEMP_MPY_wvf_snd.mp3")):
                os.remove(Path(f"{this_path}/../../{i}-videoTEMP_MPY_wvf_snd.mp3"))
            if os.path.exists(Path(f"{this_path}/../../{i}-video-not-editedTEMP_MPY_wvf_snd.mp3")):
                os.remove(Path(f"{this_path}/../../{i}-video-not-editedTEMP_MPY_wvf_snd.mp3"))

    logging.info(f'{user}: Got {l_single_posts_count} single posts, {l_carousel_count} carousel posts and {l_videos_count} videos with {l_failed_count} failed posts from "{subreddit}" subreddit')
    return l_single_posts_count, l_carousel_count, l_videos_count, l_failed_count