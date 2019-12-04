#!/usr/bin/env python3

import requests
from datetime import date, timedelta
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time


class NowListCrawler(BaseListCrawler):

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
        it return json response in this news source 
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()

    def fetch_list(self, jsonRes):
        news = []
        news_rows = jsonRes
        for row in news_rows:
            try:
                raw = {
                    'title': row['title'],
                    'url': row['link'],
                    'url_md5': md5(row['link']),
                    'source_id': 7,
                    'category': 'None'  # 先暫時不寫這欄
                }
                news.append(raw)
            except:
                continue
        return news

    def make_a_round(self):
        consecutive = 0
        # i just set a unreachable number of page, but maybe someday it will exceed
        for pageNum in range(1, 1000000):

            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break

            page_url = "https://www.nownews.com/wp-json/wp/v2/posts?page={pageNum}&per_page=100".format(pageNum=pageNum)
            print(page_url)

            # get json response
            jsonRes = self.fetch_html(page_url)

            # check if it exceeds the number of pages
            if type(jsonRes) is not list:
                if jsonRes['code'] == 'rest_post_invalid_page_number':
                    break

            # parse json data
            news_list = self.fetch_list(jsonRes)

            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1

    def run(self):
        self.make_a_round()
