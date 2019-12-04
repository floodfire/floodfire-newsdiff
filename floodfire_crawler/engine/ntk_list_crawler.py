#!/usr/bin/env python3

import requests
from datetime import date, timedelta
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time


class NtkListCrawler(BaseListCrawler):

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
        news_rows = soup.find_all("div", {"class": "news-list-item clearfix"})
        #md5hash = md5()
        for news_row in news_rows:
            try:
                link_a = news_row.find("a", class_='newsBox')
                md5hash = md5(link_a['href'].encode('utf-8')).hexdigest()
                raw = {
                    'title': news_row.find("div", class_='news_title').text.strip(),
                    'url': link_a['href'],
                    'url_md5': md5hash,
                    'source_id': 6,
                    'category': 'None'
                }
                news.append(raw)
            except:
                continue
        return news

    def make_a_round(self):
        today = date.today()
        end_day = date(2009, 8, 31)
        numdays = (today-end_day).days
        # first page
        consecutive = 0
        page_url = self.url
        print(page_url)
        sleep(2)
        html = self.fetch_html(page_url)

        soup = BeautifulSoup(html, 'html.parser')
        news_list = self.fetch_list(soup)
        # print(news_list)

        # check if the news have saved in database
        for news in news_list:
            if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                self.floodfire_storage.insert_list(news)
                consecutive = 0
            else:
                print(news['title']+' exist! skip insert.')
                consecutive += 1

        # next page
        for mydate in (today - timedelta(days=x) for x in range(numdays)):
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            page_url = "https://newtalk.tw/news/summary/" + mydate.isoformat()
            print(page_url)
            sleep(2)
            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_list = self.fetch_list(soup)
            # print(news_list)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1

    def run(self):
        self.make_a_round()
