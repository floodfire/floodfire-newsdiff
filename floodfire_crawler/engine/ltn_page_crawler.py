#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class LtnPageCrawler(BasePageCrawler):

    def __init__(self, config):
        self.code_name = "ltn"
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        """
        取出網頁 HTML 原始碼

        Keyword arguments:
            url (string) -- 抓取的網頁網址
        """
        try:
            response = requests.get(url, timeout=15)
            resp_content = {
                'redirected_url': response.url, # 取得最後 redirect 之後的真實網址
                'html': response.text
            }
        except requests.exceptions.HTTPError as err:
            msg = "HTTP exception error: {}".format(err)
            return 0, msg
        except requests.exceptions.RequestException as e:
            msg = "Exception error {}".format(e)
            return 0, msg

        return response.status_code, resp_content

    def __news_category(self, soup):
        """
        取出 news 類別需要的資料內容
        """
        page = dict()
        article_title = soup.find('div', class_='whitecon articlebody')
        page['title'] = article_title.h1.text.strip()
        article_content = soup.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article_content.find('span', class_='viewtime').text
        return page

    def __ent_category(self, soup):
        """
        取出 ent 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', itemprop='articleBody')
        page['title'] = article.h1.text.strip()
        p_tags = article.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        time_string = soup.find('meta', attrs={'name':'pubdate'})
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string['content'][:-6], '%Y-%m-%dT%H:%M:%S'))

        return page

    def __ec_category(self, soup):
        """
        取出 ec 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='whitecon boxTitle')
        page['title'] = article.h1.text.strip()
        article_content = article.find('div', class_='text')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article.find('span', class_='time').text + ':00'
        return page

    def __sports_category(self, soup):
        """
        取出 sports 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='news_content')
        page['title'] = article.h1.text.strip()
        article_content = article.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article.find('div', class_='c_time').text
        
        return page

    def __talk_category(self, soup):
        """
        取出 talk 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='conbox')
        page['title'] = article.h1.text.strip()
        article_content = article.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article.find('div', class_='writer_date').text + ':00'
        return page

    def __istyle_category(self, soup):
        """
        取出 istyle 類別需要的資料內容
        """
        page = dict()
        article_title = soup.find('div', class_='caption')
        page['title'] = article_title.h2.text.strip()
        article_content = soup.find('article').find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        
        time_string = article_title.find('div', class_='label-date').text
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string, '%b. %d %Y %H:%M:%S'))
        return page

    def __3c_category(self, soup):
        """
        取出 3c 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='conbox')
        page['title'] = article.h1.text.strip()
        article_content = article.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] =  article.find('div', class_='writer').select('span')[1].text + ':00'
        return page

    def __market_category(self, soup):
        """
        取出 market 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='whitecon articlebody boxTitle')
        page['title'] = article.h1.find('div', class_='boxText').text.strip()
        article_content = article.find('div', class_='text')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article_content.find('span', class_='date1').text
        return page

    def __auto_category(self, soup):
        """
        取出 auto 類別需要的資料內容
        """
        page = dict()
        article_title = soup.find('h1', class_='h1tt')
        page['title'] = article_title.text.strip()
        article_content = soup.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags])
        page['publish_time'] = article_content.find('span', class_='h1dt').text + ':00'
        return page

    def __playing_category(self, soup):
        """
        取出 playing 類別需要的資料內容
        """
        page = dict()
        article_title = soup.find('div', class_='article_header')
        page['title'] = article_title.h1.text.strip()
        article_content = soup.find('div', itemprop='articleBody').find('div', class_='text')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text.strip() for p in p_tags])
        time_string = soup.find('meta', property='article:published_time')
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string['content'][:-7], '%Y-%m-%dT%H:%M:%S'))
        return page
    
    def fetch_news_content(self, category, soup):
        """
        取出網頁中的新聞內容

        Keyword arguments:
            category (string) -- 類別
            soup (beautifulsoup) -- 已經 parse 過的 BeautifulSoup 物件
        """
        news_page = dict()
        if category == 'news':
            news_page = self.__news_category(soup)
        elif category == 'ent':
            news_page = self.__ent_category(soup)
        elif category == 'ec':
            news_page = self.__ec_category(soup)
        elif category == 'sports':
            news_page = self.__sports_category(soup)
        elif category == 'talk':
            news_page = self.__talk_category(soup)
        elif category == 'istyle':
            news_page = self.__istyle_category(soup)
        elif category == '3c':
            news_page = self.__3c_category(soup)
        elif category == 'market':
            news_page = self.__market_category(soup)
        elif category == 'auto':
            news_page = self.__auto_category(soup)
        elif category == 'playing':
            news_page = self.__playing_category(soup)
        return news_page
    
    def extract_type(self, url):
        """
        萃取網址 domain 第一段作為類別

        Keyword arguments:
            url (string) -- 要進行萃取的網址
        """
        hostname = urlparse(url).hostname
        page_type = hostname.split('.')[0]
        return page_type
    
    
    def run(self):
        """
        程式進入點
        """
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)
        
        for row in crawl_list:
            status_code, html_content = self.fetch_html(row['url'])
            if status_code == requests.codes.ok:
                page_type = self.extract_type(html_content['redirected_url'])

                soup = BeautifulSoup(html_content['html'], 'html.parser')
                news_page = self.fetch_news_content(page_type, soup)
                # print(news_page)
                news_page['list_id'] = row['id']
                news_page['url'] = row['url']
                news_page['url_md5'] = row['url_md5']
                news_page['redirected_url'] = html_content['redirected_url']
                news_page['source_id'] = source_id
                news_page['image'] = 0
                news_page['video'] = 0

                self.floodfire_storage.insert_page(news_page)
                # 更新爬抓次數記錄
                self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                # 隨機睡 2~6 秒再進入下一筆抓取
                print('crawling...[{}] id: {}'.format(page_type, row['id']))
                sleep(randint(2, 6))
            else:
                # get 網頁失敗的時候更新 error count
                self.floodfire_storage.update_list_errorcount(row['url_md5'])

        # 單頁測試
        # status_code, html_content = self.fetch_html('http://playing.ltn.com.tw/article/10785')
        # if status_code == requests.codes.ok:
        #     page_type = self.extract_type(html_content['redirected_url'])
        #     soup = BeautifulSoup(html_content['html'], 'html.parser')
        #     news_page = self.fetch_news_content(page_type, soup)
        #     print(news_page)