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
            self.cur = self.conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
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
            return False
        return True

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
        sql = "UPDATE `list` SET `crawler_count` = `crawler_count` + 1 WHERE `url_md5`=%s"
        try:
            self.cur.execute(sql, (url_hash,))
            self.conn.commit()

        except MySQLdb.OperationalError as e:
            print('Error! Update list crawler_count error!' + e.args[1])
            return False

        return True

    def update_list_errorcount(self, url_hash):
        """
        更新列表錯誤次數

        Keyword arguments:
            url_hash (string) -- list 代表的 hansh 值
        """
        sql = "UPDATE `list` SET `error_count` = `error_count` + 1 WHERE `url_md5`=%s"
        try:
            self.cur.execute(sql, (url_hash,))
            self.conn.commit()               

        except MySQLdb.OperationalError as e:
            print('Error! Update list error_count error!' + e.args[1])
            return False
        return True
    
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
        sql = "SELECT `id` FROM `source` WHERE `code_name`=%s"
        try:
            self.cur.execute(sql, (code_name,))
            rs = self.cur.fetchone()
            source_id = rs['id']

        except MySQLdb.OperationalError:
            print('Error! Get source id error!')
        return source_id

    def get_crawllist(self, source_id):
        """
        取得待爬的資料內容

        Keyword arguments:
            source_id (int) -- 媒體編號
        """
        rs = {}
        sql = "SELECT `id`, `url`, `url_md5` FROM `list` \
               WHERE `source_id`=%s AND `crawler_count`=0 Limit 0,50"
        try:
            self.cur.execute(sql, (source_id,))
            if self.cur.rowcount > 0:
                rs = self.cur.fetchall()                

        except MySQLdb.OperationalError as e:
            print('Error! Get crawl list error!' + e.args[1])
        return rs
    
    def insert_page(self, page_row):
        """
        新增 news page 資料

        Keyword arguments:
            page (dictionary) -- 新聞 page 的新聞內容
        """
        sql = "INSERT INTO `page`(`list_id`, `url`, `url_md5`, `redirected_url`, `source_id`, `publish_time`, `title`, `body`, `authors`, `image`, `video`, `keywords`, `created_at`) \
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (
            page_row['list_id'],
            page_row['url'],
            page_row['url_md5'],
            page_row['redirected_url'],
            page_row['source_id'],
            page_row['publish_time'],
            page_row['title'],
            page_row['body'],
            ','.join(page_row['authors']),
            page_row['image'],
            page_row['video'],
            ','.join(page_row['keywords']),
            time.strftime('%Y-%m-%d %H:%M:%S')
        )

        try:
            self.cur.execute(sql, params)
            self.conn.commit()
        except MySQLdb.OperationalError:
            print('Error! Insert new list error!')
            return False

        return True

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
