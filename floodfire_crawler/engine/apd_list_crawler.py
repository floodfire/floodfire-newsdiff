#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import json
import re

class ApdListCrawler(BaseListCrawler):

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
	
	
    def fetch_list(self, json_soup):
        news = []
        news_rows = json_soup['content_elements']
        #md5hash = md5()
        for news_row in news_rows:
            link_a = 'https://tw.appledaily.com'+news_row['websites']['tw-appledaily']['website_url']
            md5hash = md5(link_a.encode('utf-8')).hexdigest()
            raw = {
                'title': news_row['headlines']['basic'].replace('\u3000', '　'),
                'url': link_a,
                'url_md5': md5hash,
                'source_id': 1,
                'category': news_row['taxonomy']['primary_section']['name']
            }
            news.append(raw)
        return news

    def make_a_round(self):
        # 取得d值
        base_url = 'https://tw.appledaily.com/realtime/new/'
        res = requests.get(base_url)
        d_value = re.findall('\?d=[0-9]+', res.text)[0].split('=')[1]

        url = 'https://tw.appledaily.com/pf/api/v3/content/fetch/query-feed?' + \
              'query={"feedOffset":0,"feedQuery":"type:story","feedSize":"100","sort":"display_date:desc"}&'+\
              'd='+d_value+'&_website=tw-appledaily'
              
        html = self.fetch_html(url)
        json_soup = json.loads(html)
        consecutive = 0

        news_list = self.fetch_list(json_soup)
        #print(news_list)
        for news in news_list:
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break

            if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                self.floodfire_storage.insert_list(news)
                consecutive = 0
            else:
                print(news['title']+' exist! skip insert.')
                consecutive += 1


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
        
