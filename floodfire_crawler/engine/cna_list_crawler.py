#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class CnaListCrawler(BaseListCrawler):

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


        if req.status_code == requests.codes.ok:
            html = req.text
        return html

    def get_last(self):
        return null
	
	
    def fetch_list(self, soup):
        news_cat_dic = {'aipl':'政治', 'aopl':'國際', 'acn':'兩岸', 'aie':'產經', 'asc':'證券', 'ait':'科技','ahel':'生活', 
                'asoc':'社會', 'aloc':'地方', 'acul':'文化', 'aspt':'運動','amov':'娛樂'}
        news = []
        total_news_rows = soup.find_all("ul", {"id": "myMainList"})
        news_rows = total_news_rows[0].find_all('li')
        #md5hash = md5()
        for news_row in news_rows:
            category = ''
            link_a = news_row.find('a')
            if 'javascript:' in link_a['href']:
                continue
            md5hash = md5(link_a['href'].encode('utf-8')).hexdigest()
            category_eng = link_a['href'].split('/')[4]
            if category_eng in news_cat_dic:
                category = news_cat_dic[category_eng]
            else:
                category = category_eng
            raw = {
                'title': link_a.h2.text.strip().replace("　"," ").replace("\u200b",""),
                'url': link_a['href'],
                'url_md5': md5hash,
                'source_id': 10,
                'category': category
            }
            news.append(raw)
        return news

    def make_a_round(self):
        consecutive = 0
        sleep_time =0
#        start_page = 1
#        page = 1
        while(1):
            if sleep_time >10:
                print('Sleep over 10 times, stop!')
                break
#            if consecutive > 5:
#                print('News consecutive more than 20, sleep 5 min')
#                sleep_time +=1
#                sleep(5)
            """
            page_url = self.url + '/realtime/' + str(page)
            print(page_url)
            """
#            sleep(2)
#            html = self.fetch_html(page_url)
            html = self.fetch_html(self.url)
            soup = BeautifulSoup(html, 'html.parser')
            
            if(soup.contents[0]!='html'):
                break
            
            
            news_list = self.fetch_list(soup)
            #print(news_list)
            for news in news_list:

                if consecutive > 5:
                    print('News consecutive more than 20, sleep 5 min')
                    consecutive = 0
                    sleep_time +=1
                    sleep(300)
                    break 
                if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                    self.floodfire_storage.insert_list(news)
                    consecutive = 0
                else:
                    print(news['title']+' exist! skip insert.')
                    consecutive += 1
#            print('one page done !sleep 5 min!')
            sleep_time +=1
            sleep(300)
#            page += 1


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
        
