#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from base_list_crawler import BaseListCrawler

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
        news_lis = soup.find('ul', 'imm').find_all('li')
        for news_li in news_lis:
            link_a = news_li.find('a', class_='tit')
            raw = {
                'title': link_a.p.text.strip(),
                'href': link_a['href']
            }
            news.append(raw)
        return news

    def count_page(self):
        pass
    
    def run(self):
        html = self.fetch_html()
        soup = BeautifulSoup(html, 'html.parser')
        news = self.fetch_list(soup)
        print(news)

        
