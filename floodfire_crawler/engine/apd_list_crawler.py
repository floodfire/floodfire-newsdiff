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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=15)
        resp_content = response.text
        return response.status_code, resp_content

    def get_last(self):
        return None

    def fetch_list(self, soup):
        # 初始化
        news = []
        # 取得頁面列表
        news_rows = soup.find_all("div", {"id": "infScroll"})
        # 一筆一筆取得資料
        for news_row in news_rows:
            # 取得完整網址及計算其hash
            page_url = news_row.find("a")["href"]
            md5hash = md5(page_url.encode('utf-8')).hexdigest()
            # 整理其他資料
            raw = {
                'title': news_row.find("span").text.strip().replace('\u3000', '　'),
                'url': page_url,
                'url_md5': md5hash,
                'source_id': 1,
                'category': 'None'  # 頁面上沒有該欄位
            }
            news.append(raw)
        return news

    def make_a_round(self):
        consecutive = 0  # 重複次數
        page_idx = 1  # 初始頁面
        url = self.url

        while 1:
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            # 網址範例 'https://www.appledaily.com.tw/realtime/new/42'
            page_url = url+str(page_idx)
            print(page_url)
            sleep(2)

            # 取得頁面內容
            status_code, html_content = self.fetch_html(page_url)
            page_idx += 1
            if (status_code != 200):
                break

            # 拆解頁面資訊，取得列表
            soup = BeautifulSoup(html_content, 'html.parser')
            news_list = self.fetch_list(soup)
            if len(news_list) == 0:
                print('Realtime end.')
                break
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1

    def run(self):
        self.make_a_round()
