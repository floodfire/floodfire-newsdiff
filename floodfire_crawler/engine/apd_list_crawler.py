#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

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
        req = requests.get(url)

        if req.status_code == requests.codes.ok:
            html = req.text
        return html

    def get_last(self):
        return null
	
	
    def fetch_list(self, soup):
        news = []
        news_rows = soup.find_all("li", {"class": "rtddt"})
        #md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.find('a')
            md5hash = md5(link_a['href'].encode('utf-8')).hexdigest()
            raw = {
                'title': link_a.font.text.strip().replace("　"," ").replace("\u200b",""),
                'url': link_a['href'],
                'url_md5': md5hash,
                'source_id': 1,
                'category': link_a.h2.text
            }
            news.append(raw)
        return news

    def make_a_round(self):
        consecutive = 0
        start_page = 1
        page = 1
        while(1):
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            page_url = self.url + '/realtime/' + str(page)
            print(page_url)
            sleep(2)
            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            if(soup.contents[0]!='html'):
                break
            
            
            news_list = self.fetch_list(soup)
            #print(news_list)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1
            page += 1


    def run(self):
        html = self.fetch_html(self.url)
        soup = BeautifulSoup(html, 'html.parser')
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
        
