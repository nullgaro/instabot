# INSTABOT
![Icon](icon.png)

***Language***
- [🇪🇸 Español](./README.es.md)
- 🇺🇸 English

# Description

Instabot is a program developed in Python with the purpose of fully automating any Instagram account in a legal way using the Instagram API to upload posts that have been automatically fetched from reddit.

It features the ability to handle multiple accounts simultaneously with the same instance, for greater organization and convenience.

# Previous steps

## Preparing the account to be able to automate it

1. Create a [Gmail account](https://gmail.coms).

2. Create an [Instagram account](https://instagram.com).

3. Create a [Facebook account](https://facebook.com).

4. Create a [Facebook page](https://www.facebook.com/pages/creation/?ref_type=launch_point).

5. Create an [Imgur account](https://imgur.com).

6. Change the Imgur [account to developer](https://api.imgur.com/oauth2/addclient) and put in Authorization callback URL: "https://oauth.pstmn.io/v1/browser-callback". **REMEMBER to save the Client ID and Client secret in the .users.json!**

7. Through the Instagram application change the account to Business and link it to the Facebook page you created earlier. **You have to wait a few minutes from the time you create the Facebook page. Take advantage of this and go get a coffee**.

8. Log in to [Facebook developers](https://developers.facebook.com/docs/instagram/) with your Facebook account, create an application by choosing the option "Other" -> "Enterprise".
    Go to Configure -> Basic information and save the "Application identifier" and the "Application secret key" in the .users.json (id_api_insta and id_secret_api_insta).

9. Go to [API Graph Explorer](https://developers.facebook.com/tools/explorer/)
    1. Give it the [required permissions](https://developers.facebook.com/docs/instagram-api/guides/content-publishing#permisos):
        * ads_management
        * business_management
        * instagram_basic
        * instagram_content_publish
        * pages_read_engagement
    2. Generate a new token and store it in .users.json -> instagram_token

## Preparing the code environment

1. Fill in the information in `.users.json.example`. The information that would be 100% necessary:
    * instagram_token
    * id_api_imgur
    * description
    * tags
    * subreddits

2. Put the name of the user you are going to use in the `.env.example` in case you put several users continue them with a comma `USERNAME1,USERNAME2`.

3. Remove the `.example` suffix from the `.env.example` and `.users.json.example` files.

3. Install Python (only tested in version 3.10.10).

4. Install [ffmpeg](https://www.ffmpeg.org/download.html) for your operating system.

5. Open a terminal and move to the project directory.

6. Run `pip install -r requirements.txt`.

7. Generate a new Access token from [Graph API Explorer](https://developers.facebook.com/tools/explorer/) and immediately run `python3 setup.py` to get the insta_id and a LLAT (Long Live Access Token).

# Run the program

To run the program open a terminal and run `python3 main.py &`, I recommend adding the `&` to allow the program to run in the background.

# How it works

The program uses the Reddit API to download the maximum allowed posts (100 posts) from the subreddits previously annotated in the `.users.json` file and filters them according to whether they are valid for Instagram requirements, the videos are formatted for Instagram to accept them and everything downloaded is stored in a SQLite database.

When publishing the posts, the APScheduler library is used to simulate a crontab with the times given in the `.env` file and it will publish them for the users that are in the file.

Because Instagram requires a public URL to grab the post to be uploaded, we use the Imgur API to upload them and have it return a URL that will be the one we will give to the Instagram API.

## File conditions:

### Images.

```
    Up to 8MB

    Valid formats:
        image/jpg

    Aspect Ratio: Must be between 4:5 and 1.91:1


    Can be unadjusted (will be adjusted automatically by instagram)

    Minimum width: 320 px (Will be scaled up if needed)
    Maximum width: 1440 px (Will be scaled up if needed)

    Height: Varies, depends on width and aspect ratio
```

### Videos
```
    Up to 100MB
    Between 3 and 60 seconds
    Between 23 and 60 FPS

    Maximum width 1920 px

    Aspect Ratio between 4:5 and 16:9

    Valid formats:
        video/mp4
        video/mpeg
```
