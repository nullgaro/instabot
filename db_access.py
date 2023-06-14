import os
from datetime import date
from pathlib import Path

this_path = Path(__file__).parent.resolve()
import sqlite3 as sql

class SingletonDB(type):
    _instances = {}
    def __call__(self, user, *args, **kwargs):
        if (self, user) not in self._instances:
            self._instances[self, user] = super(SingletonDB, self).__call__(user, *args, **kwargs)

        return self._instances[self, user]

class DB(metaclass=SingletonDB):

    db_path = None
    conn = None
    cur = None

    def __init__(self, user):
        self.db_path = Path(f"{this_path}/{user}.db")
        self.conn = sql.connect(self.db_path, check_same_thread=False)
        self.cur = self.conn.cursor()

        if not self.checkIfTableExists("posts"):
            self.createDB()

    def _close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        self._close()


    # Create the databe and the tables
    def createDB(self):
        with self.conn:
            self.cur.execute(
                """CREATE TABLE posts (
                    file_name text NOT NULL,
                    media_url text NOT NULL PRIMARY KEY,
                    media_type text NOT NULL,
                    id_post text,
                    user text NOT NULL,
                    subreddit text NOT NULL,
                    original_post text,
                    upvotes integer,
                    comment text NOT NULL,
                    original_date text,
                    stage text,
                    imgur_url text,
                    instagram_url text,
                    date_of_publish text,
                    instagram_id text
                )"""
            )

    def checkIfTableExists(self, table):
        with self.conn:
            query = f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table}'"
            self.cur.execute(query)
            data, = self.cur.fetchone()
        return data >= 1

    # Insert only one row with the given values
    def postsInsertOneRow(self, file_name, media_url, media_type, id_post, user, subreddit, original_post, upvotes, comment, original_date):
        with self.conn:
            query = f"INSERT INTO posts VALUES ('{file_name}', '{media_url}', '{media_type}', '{id_post}', '{user}', '{subreddit}', '{original_post}', {upvotes}, '{comment}', '{original_date}', 'Scrapped', '', '', '', '')"
            self.cur.execute(query)

    # Checks if any id matches with the given id, if matches != 0, if not returns 0
    def getMachedPostUrls(self, url):
        with self.conn:
            query = f"SELECT id_post FROM posts WHERE media_url = '{url}'"
            self.cur.execute(query)
            data = self.cur.fetchall()
        return len(data)

    # Search for a post filtered by the stage
    def getOnePostStageFiltered(self, stage, priorize_todays_posts):
        with self.conn:
            if priorize_todays_posts == "True":
                query = f"SELECT file_name, media_type, comment, user, subreddit FROM posts WHERE stage = '{stage}' and original_date like '{date.today().strftime('%d/%m/%Y')}' ORDER BY RANDOM() LIMIT 1"
                self.cur.execute(query)

                if self.cur.rowcount > 0:
                    data = self.cur.fetchone()
                    return data

            query = f"SELECT file_name, media_type, comment, user, subreddit FROM posts WHERE stage = '{stage}' ORDER BY RANDOM() LIMIT 1"
            self.cur.execute(query)
            data = self.cur.fetchone()
        return data

    # Checks if there's any posts with the given stage
    def checkIfHaveAnyPostStageFiltered(self, stage):
        with self.conn:
            query = f"SELECT file_name FROM posts WHERE stage = '{stage}' LIMIT 1"
            self.cur.execute(query)
            data = self.cur.fetchone()
        return False if data is None else len(data) > 0

    # Search all the posts filtered by the stage where id_post matches with the given post and return the file_name
    def getPostsStageFilteredCarousel(self, file_name, stage):
        with self.conn:
            query = f"SELECT file_name, media_type FROM posts WHERE stage = '{stage}' and id_post = (SELECT id_post FROM posts WHERE file_name = '{file_name}')"
            self.cur.execute(query)
            data = self.cur.fetchall()
        return data

    # Seach for all the posts that matches the id_post with the given one.
    def isCarousel(self, file_name):
        with self.conn:
            query = f"SELECT count(file_name) FROM posts WHERE id_post = (SELECT id_post FROM posts WHERE file_name = '{file_name}')"
            self.cur.execute(query)
            data, = self.cur.fetchone()
        return data > 1

    # Returns the last used row
    def getLastPostNumber(self):
        with self.conn:
            query = "SELECT max(rowid) FROM posts"
            self.cur.execute(query)
            data, = self.cur.fetchone()
        return data

    def postAddedImgur(self, file_name, stage, imgur_url):
        with self.conn:
            query = f"UPDATE posts SET stage = '{stage}', imgur_url = '{imgur_url}' WHERE file_name = '{file_name}'"
            self.cur.execute(query)

    def postGetImgurUrl(self, file_name):
        with self.conn:
            query = f"SELECT imgur_url FROM posts WHERE file_name = '{file_name}'"
            self.cur.execute(query)
            data, = self.cur.fetchone()
        return data

    def postOnInstagram(self, file_name, stage, instagram_url, date_of_publish, instagram_id):
        with self.conn:
            query = f"UPDATE posts SET stage = '{stage}', instagram_url = '{instagram_url}', date_of_publish = '{date_of_publish}', instagram_id = '{instagram_id}' WHERE file_name = '{file_name}'"
            self.cur.execute(query)

    def postCarouselOnInstagram(self, file_name, stage, instagram_url, date_of_publish, instagram_id):
        with self.conn:
            query = f"UPDATE posts SET stage = '{stage}', instagram_url = '{instagram_url}', date_of_publish = '{date_of_publish}', instagram_id = '{instagram_id}' WHERE id_post = (SELECT id_post FROM posts WHERE file_name = '{file_name}')"
            self.cur.execute(query)

    def postUpdateStage(self, file_name, stage):
        with self.conn:
            query = f"UPDATE posts SET stage = '{stage}' WHERE id_post = (SELECT id_post FROM posts WHERE file_name = '{file_name}')"
            self.cur.execute(query)

    def postDeleteOneRow(self, file_name):
        with self.conn:
            query = f"DELETE FROM posts WHERE file_name = '{file_name}'"
            self.cur.execute(query)

    def clearPostsTable(self):
        with self.conn:
            query = "DELETE FROM posts"
            self.cur.execute(query)