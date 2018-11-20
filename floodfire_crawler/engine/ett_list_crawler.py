#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time

class EttListCrawler(BaseListCrawler):

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
	
	
    def fetch_list(self, soup):
        news = []
        news_rows = soup.find("div",{"class":"part_list_2"}).find_all('h3')
        #md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.a
            md5hash = md5(link_a['href'].split("?")[0].encode('utf-8')).hexdigest()
            raw = {
                'title': news_row.a.text.strip().replace("　"," ").replace("\u200b",""),
                'url': "https://www.ettoday.net"+link_a['href'].split("?")[0],
                'url_md5': md5hash,
                'source_id': 4,
                'category': news_row.em.text
            }
            news.append(raw)
        return news

    def fetch_list2(self, soup):
        news = []
        news_rows = soup.find_all('h3')
        #md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.a
            md5hash = md5(link_a['href'].split("?")[0].encode('utf-8')).hexdigest()
            raw = {
                'title': news_row.a.text.strip().replace("　"," ").replace("\u200b",""),
                'url': "https://www.ettoday.net"+link_a['href'].split("?")[0],
                'url_md5': md5hash,
                'source_id': 4,
                'category': news_row.em.text.strip().replace("　"," ").replace("\u200b","")
            }
            news.append(raw)
        return news


    def make_a_round(self):
        filter = ['政治', '地方', '影劇', '國際', '財經', '生活', '社會', '大陸', '體育', '論壇', '軍武']

        #first page
        consecutive = 0
        page_url = self.url
        print(page_url)
        sleep(2)
        html = self.fetch_html(page_url)
        
        soup = BeautifulSoup(html, 'html.parser')
        news_list = self.fetch_list(soup)
        #print(news_list)
        for news in news_list:
            if(self.floodfire_storage.check_list(news['url_md5']) == 0 and news['category'] in filter):
                self.floodfire_storage.insert_list(news)
                consecutive = 0
            else:
                print(news['title']+' exist! skip insert.')
                consecutive += 1

        #starting from page2
        offset = 1
        page_url = "https://www.ettoday.net/show_roll.php"

        while(1):
            offset = offset+1
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break

            headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }

            body = {
                'offset': offset,
                'tPage': '3',
                'tFile': time.strftime('%Y%m%d') + '.xml',
                'tOt': '0',
                'tSi': '100',
                'tAr': '0'
            }
            print(page_url+", page"+str(offset))
            sleep(2)

            req = requests.post(page_url, headers = headers, data = body, timeout = 15)
            html = req.text
            #end of the pages
            if(html == ''):
                break

            soup = BeautifulSoup(html, 'html.parser')
            news_list = self.fetch_list2(soup)
            #print(news_list)
            for news in news_list:
                if(self.floodfire_storage.check_list(news['url_md5']) == 0 and news['category'] in filter):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1


    def run(self):
        self.make_a_round()
