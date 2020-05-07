#!/usr/bin/env python3

import requests
from datetime import date, timedelta
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time


class TVBSListCrawler(BaseListCrawler):

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
        return response.json()

    def fetch_list(self, soup):

        return [{
            'url': 'https://news.tvbs.com.tw' + a['href'],
            'title': a.h2.get_text(strip=True),
            'url_md5': md5('https://news.tvbs.com.tw' + a['href']).hexdigest(),
            'source_id': 9,
            'category': 'None'
        } for a in soup.find_all('a')
            if 'https://news.tvbs.com.tw/live' not in 'https://news.tvbs.com.tw' + a['href']
        ]

    def make_a_round(self):
        today = date.today()
        end_day = date(2009, 8, 31)
        numdays = (today-end_day).days
        consecutive = 0

        # next page
        for mydate in (today - timedelta(days=x) for x in range(numdays)):
            newsOffset = 6
            URL = f"https://news.tvbs.com.tw/news/LoadMoreOverview_realtime?showdate={mydate}&newsoffset={newsOffset}&ttalkoffset=0&liveoffset=0"

            print(URL)
            html = self.fetch_html(URL)
            soup = BeautifulSoup(html['add_li'], 'html.parser')
            news_list = self.fetch_list(soup)

            while(len(news_list) % 6 == 0):
                print(URL)
                sleep(2)
                html = self.fetch_html(URL)
                soup = BeautifulSoup(html['add_li'], 'html.parser')
                news_list.extend(self.fetch_list(soup))

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

    def run(self):
        self.make_a_round()
