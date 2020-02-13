#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time
import json

class UdnListCrawler(BaseListCrawler):

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    def __init__(self, config):
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        return html

    def get_last(self):
        return None
	
	
    def fetch_list(self, soup_json):
        news = []
        news_rows = soup_json['lists']
        #md5hash = md5()
        for news_row in news_rows:
            md5hash = md5(news_row['titleLink'].encode('utf-8')).hexdigest()
            raw = {
                'title': news_row['title'],
                'url': "https://udn.com"+news_row['titleLink'],
                'url_md5': md5hash,
                'source_id': 8,
                'category': 'None' #新的API找不到解析欄位
            }
            news.append(raw)
        return news

    def make_a_round(self):
        #first page
        consecutive = 0
        base_url = 'https://udn.com/api/more?id=&channelId=1&cate_id=0&type=breaknews&page='
        now_page = 1
        while(1):
            page_url = base_url + str(now_page)
            html = self.fetch_html(page_url)
            soup_json = json.loads(html)
            if ('lists' not in soup_json):
                break

            news_list = self.fetch_list(soup_json)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            sleep(2)
            now_page = now_page + 1

    def run(self):
        self.make_a_round()
        """
        news_list = self.fetch_list(soup)
        print(news_list)
        for news in news_list:
            if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                self.floodfire_storage.insert_list(news)
            else:
                print(news['title']+' exist! skip insert.')
            
        last_page = self.get_last(soup)
        print(last_page)
        """
        
