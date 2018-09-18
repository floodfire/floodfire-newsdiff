#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from floodfire_crawler.core.base_list_crawler import BaseListCrawler

class LtnListCrawler(BaseListCrawler):

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    def fetch_html(self):
        req = requests.get(self.url)

        if req.status_code == requests.codes.ok:
            html = req.text
        return html

    def fetch_list(self, soup):
        news = []
        news_rows = soup.find('ul', 'imm').find_all('li')
        md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.find('a', class_='tit')
            md5hash.update(link_a['href'].encode('utf-8'))
            raw = {
                'title': link_a.p.text.strip(),
                'url': link_a['href'],
                'url_md5': md5hash.hexdigest(),
                'source_id': 5,
                'category': self.get_category(news_row)
            }
            news.append(raw)
        return news

    def count_page(self):
        pass

    def get_category(self, news_row):
        cate_list = []
        categories = news_row.find('div', class_='tagarea').find_all('a')
        for category in categories:
            cate_list.append(category.text)
        return ','.join(cate_list)

    def run(self):
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')
        news = self.fetch_list(soup)
        print(news)

        
