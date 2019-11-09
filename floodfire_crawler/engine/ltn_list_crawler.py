#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from urllib.parse import urljoin
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import json

class LtnListCrawler(BaseListCrawler):

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    def __init__(self, config):
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        """
        傳回 List 頁面的 HTML
        """
        try:
            headers = {
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }

            response = requests.get(url, headers=headers, timeout=15)
            resp_content = response.text
        except requests.exceptions.HTTPError as err:
            msg = "HTTP exception error: {}".format(err)
            return 0, msg
        except requests.exceptions.RequestException as e:
            msg = "Exception error {}".format(e)
            return 0, msg
    
        return response.status_code, resp_content

    def fetch_list(self, soup):
        """
        傳回 HTML 中所有的新聞 List
        """
        news = []
        news_rows = json.loads(soup.text)['data']
        if (type(news_rows) != list):
            news_rows = list(news_rows.values())

        if len(news_rows) == 0:
            return news
        
        for news_row in news_rows:
            md5hash = md5(news_row['url'].encode('utf-8')).hexdigest()
            raw = {
                'title': news_row['title'],
                'url': news_row['url'],
                'url_md5': md5hash,
                'source_id': 5,
                'category': news_row['type_cn']
            }
            news.append(raw)
        return news

    def get_last(self, soup):
        pass

    def make_a_round(self):
        """
        指定頁面區間抓取
        Keyword arguments:
            start_page (int) -- 起始頁面
            end_page (int) -- 結束頁面
        """
        consecutive = 0
        page_idx = 1
        url = self.url

        while 1:
            page_url = url+str(page_idx)
            print(page_url)
            sleep(2)

            status_code, html_content = self.fetch_html(page_url)
            page_idx+=1
            if (status_code != 200):
                break
            
            soup = BeautifulSoup(html_content, 'html.parser')
            news_list = self.fetch_list(soup)
            if len(news_list) == 0:
                print('Realtime end.')
                break
            print(len(news_list))
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1
                if consecutive > 20:
#                    print('News consecutive more than 20, stop crawler!!')
                    break
            if consecutive > 20:
                    print('News consecutive more than 20, stop crawler!!')
                    break

    def run(self):
        self.make_a_round()
