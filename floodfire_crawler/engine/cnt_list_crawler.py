#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from urllib.parse import urljoin
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class CntListCrawler(BaseListCrawler):

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    def __init__(self, config):
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        """
        傳回 List 頁面的 HTML
        """
        try:
            url = url.replace('https://www.chinatimes.com', 'http://34.81.224.1')
            headers = {
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }

            response = requests.get(url, headers=headers, timeout=15)
            resp_content = response.text
        except requests.exceptions.HTTPError as err:
            msg = "HTTP exception error: {}".format(err)
            return 0, msg
        except requests.exceptions.RequestException as e:
            msg = "Exception error {}".format(e)
            return 0, msg
    
        return response.status_code, resp_content

    def fetch_list(self, soup):
        """
        傳回 HTML 中所有的新聞 List
        """
        news = []
        news_rows = soup.find('section', class_='article-list').find_all('li')
        for news_row in news_rows:
            link_title = news_row.find('h3')
            if(news_row.find('h3') is None):
                continue
            link_a = link_title.find('a')
            link_url = urljoin(self.url, link_a['href'])
            md5hash = md5(link_url.encode('utf-8')).hexdigest()
            raw = {
                'title': link_title.text.strip(),
                'url': link_url,
                'url_md5': md5hash,
                'source_id': 2,
                'category': self.get_category(news_row)
            }
            news.append(raw)
        return news
    
    def get_category(self, news_row):
        """
        取得新聞分類
        """
        cate_list = []
        categories = news_row.find('div', class_='category').find_all('a')
        for category in categories:
            cate_list.append(category.text.strip())
        return ','.join(cate_list)

    def make_a_round(self, start_page, end_page):
        """
        指定頁面區間抓取
        Keyword arguments:
            start_page (int) -- 起始頁面
            end_page (int) -- 結束頁面
        """
        consecutive = 0
        for page in range(start_page, end_page+1):
            # 如果連續超過 20 組就停止
            if consecutive > 20:
                    print('News consecutive more than 20, stop crawler!!')
                    break
            page_url = self.url + '?page=' + str(page)
            print(page_url)
            sleep(2)

            status_code, html_content = self.fetch_html(page_url)
            if status_code == requests.codes.ok:
                soup = BeautifulSoup(html_content, 'html.parser')
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
        """
        程式執行點
        """
        status_code, html_content = self.fetch_html(self.url)
        if status_code == requests.codes.ok:
            soup = BeautifulSoup(html_content, 'html.parser')
            # print(self.fetch_list(soup))
            last_page = 10
            self.make_a_round(1, last_page)