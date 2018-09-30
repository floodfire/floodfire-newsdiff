#!/usr/bin/env python3

import MySQLdb
import time

class FloodfireStorage():
    def __init__(self, config):
        try:
            self.conn = MySQLdb.connect(host=config['RDB']['DB_HOST'],
                                        port=int(config['RDB']['DB_PORT']),
                                        user=config['RDB']['DB_USER'],
                                        passwd=config['RDB']['DB_PASSWORD'],
                                        db=config['RDB']['DB_DATABASE'],
                                        charset='utf8')
            self.cur = self.conn.cursor()
        except MySQLdb.OperationalError:
            print('Database connection fail!')

    def insert_list(self, news_row):
        sql = "INSERT INTO `list` (`url`, `url_md5`, `source_id`, `category`, `title`, `created_at`)\
               VALUES (%s, %s, %s, %s, %s, %s);"
        params = (
            news_row['url'],
            news_row['url_md5'],
            news_row['source_id'],
            news_row['category'],
            news_row['title'],
            time.strftime('%Y-%m-%d %H:%M:%S')
        )

        try:
            self.cur.execute(sql, params)
            self.conn.commit()
        except MySQLdb.OperationalError:
            print('Error! Insert new list error!')

    def check_list(self, url_hash):
        """
        檢查 list 是否已經存在

        Keyword arguments:
            url_hash (string) -- list 代表的 hansh 值

        Returns:
            url_hash 查詢到的筆數
        """
        sql = "SELECT * FROM `list` WHERE `url_md5`=%s"
        try:
            self.cur.execute(sql, (url_hash,))
            row_count = self.cur.rowcount

        except MySQLdb.OperationalError:
            print('Error! Insert new list error!')
        return row_count

    def update_list_crawlercount(self, url_hash):
        """
        更新列表抓取次數

        Keyword arguments:
            url_hash (string) -- list 代表的 hansh 值
        """
        pass
    
    def get_source_list(self):
        """
        取得所有媒體列表

        Returns:
            所有系統中的媒體清單 dictionary
        """
        pass

    def get_source_id(self, code_name):
        """
        由代號取得 media source 編號

        Keyword arguments:
            code_name (string) -- 媒體簡寫英文名稱
        """
        pass

    def insert_page(self, page_row):
        """
        新增 news page 資料

        Keyword arguments:
            page (dictionary) -- 新聞 page 的新聞內容
        """
        pass

    def insert_page_raw(self, html_raw):
        """
        新增 news page 的原始 html 資料

        Keyword arguments:
            html_raw (string) -- 新聞頁原始 HTML 資料內容
        """
        pass
    
    def __del__(self):
        self.cur.close()
        self.conn.close()
