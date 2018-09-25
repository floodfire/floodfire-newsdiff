#!/usr/bin/env python3

import MySQLdb
import time

class FloodfireStorage():
    def __init__(self, config):
        try:
            self.conn = MySQLdb.connect(host=config['RDB']['DB_HOST'],
                                        port=config['RDB']['DB_PORT'],
                                        user=config['RDB']['DB_USER'],
                                        passwd=config['RDB']['DB_PASSWORD'],
                                        db=config['RDB']['DB_DATABASE'],
                                        charset='utf8')
            self.cur = self.conn.cursor()
        except MySQLdb.OperationalError:
            print('Database connection fail!')

    def insert_list(self, news_row):
        sql = "INSERT INTO `list` (`url`, `url_md5`, `source_id`, `category`, `created_at`)\
               VALUES (:url, :url_md5, :source_id, :category, :created_at);"
        params = {
            "url": news_row['url'],
            "url_md5": news_row['url_md5'],
            "source_id": news_row['source_id'],
            "category": news_row['category'],
            "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        try:
            self.cur.execute(sql, params)
        except MySQLdb.OperationalError:
            print('Error! Insert new list error!')

    def check_list(self, url_hash):
        pass

    def get_source_list(self):
        pass

    def get_source_id(self, code_name):
        pass

    def __del__(self):
        self.cur.close()
        self.conn.close()