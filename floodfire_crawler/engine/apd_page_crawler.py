#!/usr/bin/env python3

import requests
import re
import htmlmin
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
from floodfire_crawler.service.diff import FloodfireDiff


class ApdPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "apd"
        self.floodfire_storage = FloodfireStorage(config)
        self.logme = logme

    def fetch_html(self, url):
        """
        取得網頁 Json 格式文章資料
        Keyword arguments:
            url (string) -- 抓取的網頁網址
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }
            # 將原文章網址換成該篇文章的 API endpoint
            url = self.transform(url)
            response = requests.get(url, headers=headers, timeout=15)
            resp_content = {
                'redirected_url': response.url,  # 取得最後 redirect 之後的真實網址
                'json': response.json()
            }
        except requests.exceptions.HTTPError as err:
            msg = "HTTP exception error: {}".format(err.args[1])
            self.logme.error(msg)
            return 0, msg
        except requests.exceptions.RequestException as e:
            msg = "Exception error {}".format(e.args[1])
            self.logme.error(msg)
            return 0, msg

        return response.status_code, resp_content

    def fetch_news_content(self, res_json):
        report = {}
        # --- 取出標題 ---
        report['title'] = res_json['content_elements'][0]['headlines']['basic']

        # --- 取出內文 ---
        article = [d['content'] for d in res_json['content_elements'][0]['content_elements'] if d['type'] == 'raw_html'][0].replace("<br>", "\n").replace("<br />", "\n")
        soup = BeautifulSoup(article, 'lxml')
        report['body'] = soup.get_text()

        # --- 取出記者 ---
        # (XXX/XX報導) (曾珮瑛、張世瑜/高雄報導) https://regex101.com/r/DvppFX/1
        author = re.search(r'[(（](.*?中心)?(.*?)(／|\/|╱)(.*?)報導[）)]', report['body'])
        if author is not None:
            report['authors'] = [author.group(2)]
        else:
            report['authors'] = ['Cannot find in report']

        # --- 取出發布時間 ---
        report['publish_time'] = self.fetch_publish_time(res_json['content_elements'][0]['last_updated_date'])

        # --- 取出關鍵字 ---
        report['keywords'] = [tag['text'] for tag in res_json['content_elements'][0]['taxonomy']['tags']]

        # --- 取出圖片數 ---
        image = [d for d in res_json['content_elements'][0]['content_elements'] if d['type'] == 'image']
        report['image'] = len(image)

        report['visual_contents'] = list()
        # -- 取出視覺資料連結（圖片） ---
        report['visual_contents'] = [{
            'type': 1,
            'visual_src': i['url'],
            'caption': i['caption']
        } for i in image]

        video = res_json['content_elements'][0]['promo_items']['basic']
        if video['type'] == 'video':
            report['video'] = 1
            # -- 取出視覺資料連結（影片） ---
            report['visual_contents'].append({
                'type': 2,
                'visual_src': video['streams'][0]['url'],
                'caption': 'video_id:' + video['additional_properties']['video_id']
            })
        else:
            report['video'] = 0

        return report

    def fetch_publish_time(self, timeString):
        # timeString e.g 2019-12-24T13:03:18.419Z
        news_time = strftime('%Y-%m-%d %H:%M:%S', strptime(timeString, '%Y-%m-%dT%H:%M:%S.%fZ'))
        return(news_time)

    def transform(self, inUrl):

        outUrl = None
        test = re.search(r'\/(\d{7})\/', inUrl)
        if(test != None):
            mId = test.group(1)
            outUrl = 'https://tw.appledaily.com/pf/api/v3/content/fetch/content-by-motherlode-id?query=%7B%22id%22%3A%221_{mId}%22%2C%22website_url%22%3A%22tw-appledaily%22%7D'.format(
                mId=mId)

        t = re.search(r'\/([[:upper:],0-9]{26})\/', inUrl)
        if(t != None):
            Id = t.group(1)
            outUrl = 'https://tw.appledaily.com/pf/api/v3/content/fetch/content-by-id?query=%7B%22id%22%3A%22{id}%22%2C%22published%22%3Atrue%2C%22website_url%22%3A%22tw-appledaily%22%7D'.format(
                id=Id)
        return outUrl

    def compress_html(self, page_json):
        """
        Deprecated in this news source
        """
        return page_json

    def run(self, page_raw=False, page_diff=False, page_visual=False):
        """
        程式進入點
        """
        # crawl_category = ['news', 'ent', 'ec', 'sports']
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        ######Diff#######
        if page_diff:
            diff_obj = FloodfireDiff()
        else:
            diff_obj = None
        version = 1
        table_name = None
        diff_vals = (version, None, None)
        ######Diff#######
        crawl_list = self.floodfire_storage.get_crawllist(source_id, page_diff, diff_obj)
        # log 起始訊息
        start_msg = 'Start crawling ' + str(len(crawl_list)) + ' ' + self.code_name + '-news lists.'
        if page_raw:
            start_msg += ' --with save RAW'
        if page_visual:
            start_msg += ' --with save VISUAL_LINK'
        self.logme.info(start_msg)
        # 本次的爬抓計數
        crawl_count = 0

        for row in crawl_list:
            try:
                status_code, html_content = self.fetch_html(row['url'])
                if status_code == requests.codes.ok:
                    print('crawling... id: {}'.format(row['id']))

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw['list_id'] = row['id']
                        news_page_raw['url'] = row['url']
                        news_page_raw['url_md5'] = row['url_md5']
                        news_page_raw['page_content'] = json.dumps(html_content['json'])
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print('Save ' + str(row['id']) + ' page Raw.')

                    # soup = BeautifulSoup(html_content['html'], 'html.parser')
                    resjson = html_content['json']
                    if(len(resjson['content_elements']) == 0):
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])
                        continue
                    news_page = self.fetch_news_content(resjson)
                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id

                    ######Diff#######
                    if page_diff:
                        last_page, table_name = self.floodfire_storage.get_last_page(news_page['url_md5'],
                                                                                     news_page['publish_time'],
                                                                                     diff_obj.compared_cols)
                        if last_page != None:
                            diff_col_list = diff_obj.page_diff(news_page, last_page)
                            if diff_col_list is None:
                                # 有上一筆，但沒有不同，更新爬抓次數，不儲存
                                print('has last, no diff')
                                crawl_count += 1
                                self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                                continue
                            else:
                                # 出現Diff，儲存
                                version = last_page['version'] + 1
                                last_page_id = last_page['id']
                                diff_cols = ','.join(diff_col_list)
                                diff_vals = (version, last_page_id, diff_cols)
                    ######Diff#######
                    print(diff_vals)
                    if self.floodfire_storage.insert_page(news_page, table_name, diff_vals):
                        # 更新爬抓次數記錄
                        self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                        self.floodfire_storage.update_list_versioncount(row['url_md5'])
                        # 本次爬抓計數+1
                        crawl_count += 1
                    else:
                        # 更新錯誤次數記錄
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])

                    # 儲存圖片或影像資訊
                    if page_visual and len(news_page['visual_contents']) > 0:
                        for vistual_row in news_page['visual_contents']:
                            vistual_row['list_id'] = row['id']
                            vistual_row['url_md5'] = row['url_md5']
                            self.floodfire_storage.insert_visual_link(vistual_row, version)

                    # 隨機睡 2~6 秒再進入下一筆抓取
                    sleep(randint(2, 6))
                else:
                    # get 網頁失敗的時候更新 error count
                    self.floodfire_storage.update_list_errorcount(row['url_md5'])
            except Exception as e:
                self.logme.exception('error: list-' + str(row['id']) + ' ' + str(e.args))
                # 更新錯誤次數記錄
                self.floodfire_storage.update_list_errorcount(row['url_md5'])
                pass
        self.logme.info('Crawled ' + str(crawl_count) + ' ' + self.code_name + '-news lists.')
