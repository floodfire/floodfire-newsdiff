#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
import time

class UdnListCrawler(BaseListCrawler):

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
        news_rows = soup.find_all("dt", {"class": "lazyload"})
        #md5hash = md5()
        for news_row in news_rows:
            link_a = news_row.find_all("a")[0]
            md5hash = md5(link_a['href'].split("?")[0].encode('utf-8')).hexdigest()
            raw = {
                'title': news_row.find_all("a")[-1].text.strip().replace("　"," ").replace("\u200b",""),
                'url': "https://udn.com"+link_a['href'].split("?")[0],
                'url_md5': md5hash,
                'source_id': 8,
                'category': news_row.find_all("a")[-2].text.strip().replace("　"," ").replace("\u200b","")
            }
            news.append(raw)
        return news

    def make_a_round(self):
        watch_list = ['社會', '生活', '地方', '全球', '要聞', '文教', '產經', '兩岸', '運動', '股市', '評論', '娛樂']

        #first page
        consecutive = 0
        page_url = self.url
        print(page_url)
        sleep(2)
        html = self.fetch_html(page_url)
        #time stamp for next pages
        stamp = round(time.time()*1000)
        
        soup = BeautifulSoup(html, 'html.parser')
        news_list = self.fetch_list(soup)
        #print(news_list)
        for news in news_list:
            if(news['category'] in watch_list and self.floodfire_storage.check_list(news['url_md5']) == 0):
                self.floodfire_storage.insert_list(news)
                consecutive = 0
            else:
                print(news['title']+' exist! skip insert.')
                consecutive += 1

        total_pages = int(soup.find_all("div",{"class":"showmore"})[0].a['data-totalpages'])

        #next page
        for page in range(2, total_pages+1):
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            page_url = "https://udn.com/news/get_breaks_article/"+str(page)+"/1/0?_="+str(stamp+page)
            print(page_url)
            sleep(2)
            html = self.fetch_html(page_url)
            soup = BeautifulSoup(html, 'html.parser')
            news_list = self.fetch_list(soup)
            #print(news_list)
            for news in news_list:
                if(news['category'] in filter and  self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1
            page += 1


    def run(self):
        self.make_a_round()
