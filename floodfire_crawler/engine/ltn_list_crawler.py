#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

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
        req = requests.get(url)

        if req.status_code == requests.codes.ok:
            html = req.text
        return html

    def fetch_list(self, soup):
        news = []
        news_rows = soup.find('ul', 'imm').find_all('li')
        #md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.find('a', class_='tit')
            md5hash = md5(link_a['href'].encode('utf-8')).hexdigest()
            raw = {
                'title': link_a.p.text.strip(),
                'url': link_a['href'],
                'url_md5': md5hash,
                'source_id': 5,
                'category': self.get_category(news_row)
            }
            news.append(raw)
        return news

    def get_last(self, soup):
        last_a_tag = soup.find('div', class_='pagination').find('a', class_='p_last')
        href_uri = last_a_tag['href']
        last_page = href_uri.rsplit('/', 1)[-1]
        return int(last_page)

    def get_category(self, news_row):
        cate_list = []
        categories = news_row.find('div', class_='tagarea').find_all('a')
        for category in categories:
            cate_list.append(category.text)
        return ','.join(cate_list)

    def make_a_round(self, start_page, end_page):
        consecutive = 0
        for page in range(start_page, end_page+1):
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            page_url = self.url + '/all/' + str(page)
            print(page_url)
            sleep(2)
            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_list = self.fetch_list(soup)
            #print(news_list)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1


    def run(self):
        html = self.fetch_html(self.url)
        soup = BeautifulSoup(html, 'html.parser')
        last_page = self.get_last(soup)
        self.make_a_round(1, last_page)
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
        
