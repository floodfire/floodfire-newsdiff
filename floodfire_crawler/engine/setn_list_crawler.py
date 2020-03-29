#!/usr/bin/env python3

import requests
from datetime import date, timedelta
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time
import re


class SetnListCrawler(BaseListCrawler):

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        return response.text

    def fetch_list(self, soup):
        news = []
        news_rows = [news for news in
                     soup.find('div', class_='NewsList').find_all('div', class_='col-sm-12')
                     if re.match(r'https:\/\/watch\.setn\.com', news.find('a', 'gt')['href']) is None
                     ]

        for news_row in news_rows:
            try:
                link = 'https://www.setn.com/' + news_row.find('a', 'gt')['href']
                raw = {
                    'title': news_row.find('a', 'gt').get_text(strip=True),
                    'url': link,
                    'url_md5': md5(link.encode('utf-8')).hexdigest(),
                    'source_id': 15,
                    'category': news_row.find('div', 'newslabel-tab').a.get_text(strip=True)
                }
                news.append(raw)
            except:
                continue
        return news

    def make_a_round(self):
        consecutive = 0
        pageNum = 1
        # next page
        while(1):

            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break

            page_url = "https://www.setn.com/ViewAll.aspx?p={pageNum}".format(pageNum=pageNum)
            print(page_url)
            pageNum += 1
            sleep(2)

            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_list = self.fetch_list(soup)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1

    def run(self):
        self.make_a_round()
