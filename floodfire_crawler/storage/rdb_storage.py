#!/usr/bin/env python3

import MySQLdb
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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

    def update_list_versioncount(self, url_hash):
        """
        更新列表版本次數

        Keyword arguments:
            url_hash (string) -- list 代表的 hansh 值
        """
        sql = "UPDATE `list` SET `version_count` = `version_count` + 1 WHERE `url_md5`=%s"
        try:
            self.cur.execute(sql, (url_hash,))
            self.conn.commit()

        except MySQLdb.OperationalError as e:
            print('Error! Update list crawler_count error!' + e.args[1])
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

    def get_crawllist(self, source_id, page_diff = False, diff_obj = None):
        """
        取得待爬的資料內容

        Keyword arguments:
            source_id (int) -- 媒體編號
            page_diff (boolean) -- 是否要Diff
        """
        rs = {}
        # Diff時，限定未爬過，或是爬過但在24小時內的list
        if page_diff and diff_obj is not None:
            sql = "SELECT `id`, `url`, `url_md5`, `crawler_count`, `category` FROM `list` \
                WHERE `source_id`=%s AND `error_count` < 5 AND \
                (`crawler_count`= 0 OR `created_at` >= %s)"
            yesterday_time = (datetime.now()+timedelta(-1)).strftime("%Y-%m-%d %H:%M:%S")
            try:
                self.cur.execute(sql, (source_id, yesterday_time,))
                if self.cur.rowcount > 0:
                    rs = self.cur.fetchall()
                    # Diff時，在黑名單中的類別只會抓第一次
                    bl = diff_obj.black_list[int(source_id)]
                    rs = [x for x in rs if x['crawler_count']==0 or sum([y in x['category'] for y in bl])  == 0]
            except MySQLdb.OperationalError as e:
                print('Error! Get crawl list error!' + e.args[1])
        else:
            sql = "SELECT `id`, `url`, `url_md5` FROM `list` \
                WHERE `source_id`=%s AND `crawler_count`= 0 AND `error_count` < 5 Limit 0,50"
            try:
                self.cur.execute(sql, (source_id,))
                if self.cur.rowcount > 0:
                    rs = self.cur.fetchall()

            except MySQLdb.OperationalError as e:
                print('Error! Get crawl list error!' + e.args[1])
        return rs

    def get_last_page(self, url_hash, publish_time, compared_cols = '*'):
        """
        取得最後一筆頁面資料

        Keyword arguments:
            url_hash (string) -- page 代表的 hansh 值
            publish_time (string) -- page的發布時間
        """
        page_data = None
        # 找上一筆的順序：當前月份表->前一個月份表->原始表
        time_obj = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
        table_names = ['page_'+publish_time[:7].replace('-','_'),
                       'page_'+(time_obj + relativedelta(months=-1)).strftime("%Y_%m"),
                       'page']
        column_str = '`'+'`, `'.join(compared_cols)+'`'
        exist_table = None
        for table_name in table_names:
            sql = "SELECT `id`, `version`," + column_str + " FROM `"+table_name+"` \
                WHERE `url_md5`=%s ORDER BY `created_at` DESC limit 1;"
            try:
                self.cur.execute(sql, (url_hash, ))
                if self.cur.rowcount > 0:
                    rs = self.cur.fetchall()
                    page_data = rs[0]
                    exist_table = table_name
                    break
            except MySQLdb.ProgrammingError as e:
                if (e.args[0]!=1146):
                    print(e.args[0], e.args[1])
                    print('Error! Get last page error!' + e.args[1])
                    continue
            except MySQLdb.OperationalError as e:
                print('Error! Get last page error!' + e.args[1])
                continue
        return page_data, exist_table

    def insert_page(self, page_row, table_name = None, diff_vals = (1, None, None)):
        """
        新增 news page 資料

        Keyword arguments:
            page_row (dictionary) -- 新聞 page 的新聞內容
            page_diff (boolean) -- 是否要Diff            
        """
        if table_name is None:
            table_name = 'page_'+page_row['publish_time'][:4]+'_'+page_row['publish_time'][5:7]

        sql = "INSERT INTO `"+table_name+"`(`list_id`, `url`, `url_md5`, `redirected_url`, `source_id`, \
        `publish_time`, `title`, `body`, `authors`, `image`, `video`, `keywords`, `created_at`, \
        `version`, `last_page_id`, `diff_cols`) \
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        default_params = (
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

        params = default_params + diff_vals

        try:
            self.cur.execute(sql, params)
            self.conn.commit()
        except MySQLdb.ProgrammingError as e:
            print(e.args[0], e.args[1])
            if (e.args[0]==1146):
                # 如果為儲存table不存在，則創建新的，然後再嘗試儲存
                if self.create_page_table(table_name):
                    try:
                        self.cur.execute(sql, params)
                        self.conn.commit()
                    except MySQLdb.OperationalError as e:
                        print('Error! Insert new page error!')
                        return False
            else:
                print('Error! Insert new page error!')
                return False                
        except MySQLdb.OperationalError:
            print('Error! Insert new page error!')
            return False

        return True

    def insert_page_raw(self, html_raw):
        """
        新增 news page 的原始 html 資料

        Keyword arguments:
            html_raw (string) -- 新聞頁原始 HTML 資料內容
        """
        sql = "INSERT INTO `page_raw`(`link_id`, `url`, `url_md5`, `page_content`, `created_at`) \
               VALUES (%s, %s, %s, %s, %s)"
        params = (
            html_raw['list_id'],
            html_raw['url'],
            html_raw['url_md5'],
            html_raw['page_content'],
            time.strftime('%Y-%m-%d %H:%M:%S')
        )

        try:
            self.cur.execute(sql, params)
            self.conn.commit()
        except MySQLdb.OperationalError:
            print('Error! Insert new html_raw error!')
            return False
        return True

    def insert_visual_link(self, visual_row, version = 1):
        """
        新增 news page 的原始 media link 資料

        Keyword arguments:
            media_row (dictionary) -- 新聞頁原始 HTML 資料內容
        """
        sql = "INSERT INTO `visual_link`(`type`, `list_id`, `url_md5`, `visual_src`, `caption`, `created_at`, `version`) \
               VALUES (%s, %s, %s, %s, %s, %s, %s)"
        params = (
            visual_row['type'],
            visual_row['list_id'],
            visual_row['url_md5'],
            visual_row['visual_src'],
            visual_row['caption'],
            time.strftime('%Y-%m-%d %H:%M:%S'),
            str(version)
        )

        try:
            self.cur.execute(sql, params)
            self.conn.commit()
        except MySQLdb.OperationalError:
            print('Error! Insert new html_raw error!')
            return False
        return True

    def create_page_table(self, table_name):
        """
        新增一個新的page table

        Keyword arguments:
            table_name (string) -- 新的table的名稱
        """
        sql = "CREATE TABLE `" + table_name + "` ( \
                `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, \
                `list_id` int(10) UNSIGNED NOT NULL COMMENT '列表編號', \
                `url` varchar(1024) NOT NULL COMMENT '新聞網址', \
                `url_md5` varchar(32) NOT NULL COMMENT '網址MD5雜湊值', \
                `redirected_url` varchar(1024) NOT NULL COMMENT '重新導向後的網址', \
                `source_id` tinyint(3) UNSIGNED NOT NULL COMMENT '媒體編號', \
                `publish_time` datetime NOT NULL COMMENT '發佈時間', \
                `title` text NOT NULL COMMENT '新聞標題', \
                `body` text NOT NULL COMMENT '新聞內容', \
                `authors` varchar(255) DEFAULT NULL COMMENT '作者（記者）', \
                `image` tinyint(1) NOT NULL DEFAULT 0 COMMENT '有無圖片', \
                `video` tinyint(1) NOT NULL DEFAULT 0 COMMENT '有無影片', \
                `keywords` varchar(255) DEFAULT NULL COMMENT '新聞關鍵字', \
                `created_at` datetime DEFAULT NULL COMMENT '建立時間', \
                `version` tinyint(4) NOT NULL DEFAULT 1 COMMENT '第幾個版本', \
                `last_page_id` int(11) DEFAULT NULL COMMENT '前一個版本的page_id', \
                `diff_cols` varchar(255) DEFAULT NULL COMMENT '跟前一個版本的差異欄位' \
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"

        try:
            self.cur.execute(sql)
            self.conn.commit()
            print('Create table succeed!')
        except MySQLdb.OperationalError:
            print('Error! Create New Table Error!')
            return False
        return True

    def __del__(self):
        self.cur.close()
        self.conn.close()
