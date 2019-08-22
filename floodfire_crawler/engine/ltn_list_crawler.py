#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from urllib.parse import urljoin
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
        """
        傳回 List 頁面的 HTML
        """
        try:
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
        news_rows = soup.find('ul', 'imm').find_all('li')
        #md5hash = md5()
        for news_row in news_rows:
            # if news_row.has_attr('id'):
            #     print('AD')
            link_a = news_row.find('a', class_='tit')
            # 20190111 自由時報加入廣告欄位，廣告內容無 a tag
            if link_a is None:
                continue
            md5hash = md5(link_a['href'].encode('utf-8')).hexdigest()
            raw = {
                'title': link_a.p.text.strip(),
                'url': urljoin(self._url, link_a['href']),
                'url_md5': md5hash,
                'source_id': 5,
                'category': self.get_category(link_a['href'])
            }
            news.append(raw)
        return news

    def get_last(self, soup):
        """
        取得頁面中的最後一頁
        """
        last_a_tag = soup.find('div', class_='pagination').find('a', class_='p_last')
        href_uri = last_a_tag['href']
        last_page = href_uri.rsplit('/', 1)[-1]
        return int(last_page)

    def get_category(self, url):
        """
        取得新聞分類
        """
        if(url.split('/')[2].split('.')[0] != 'news'):
            return url.split('/')[2].split('.')[0]
        else:
            return url.split('/')[4]

    def make_a_round(self, start_page, end_page):
        """
        指定頁面區間抓取
        Keyword arguments:
            start_page (int) -- 起始頁面
            end_page (int) -- 結束頁面
        """
        consecutive = 0
        for page in range(start_page, end_page+1):
            if consecutive > 20:
                print('News consecutive more than 20, stop crawler!!')
                break
            page_url = self.url + '/all/' + str(page)
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
        status_code, html_content = self.fetch_html(self.url)
        if status_code == requests.codes.ok:
            soup = BeautifulSoup(html_content, 'html.parser')
            last_page = self.get_last(soup)
            self.make_a_round(1, last_page)
        
