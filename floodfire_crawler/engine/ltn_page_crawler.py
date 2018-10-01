#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class LtnPageCrawler(BasePageCrawler):

    def __init__(self, config):
        self.code_name = "ltn"
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        response = requests.get(url)

        if response.status_code == requests.codes.ok:
            html = response.text
        
        # 取得最後 redirect 之後的真實網址
        last_url = response.url
        return last_url, html

    def fetch_news_content(self, category, soup):
        news_page = {}
        if category == 'news':
            article_title = soup.find('div', class_='whitecon articlebody')
            news_page['title'] = article_title.h1.text.strip()
            article_content = soup.find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article_content)
        elif category == 'ent':
            article = soup.find('div', itemprop='articleBody')
            news_page['title'] = article.h1.text.strip()
            p_tags = article.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article)
        elif category == 'ec':
            article = soup.find('div', class_='whitecon boxTitle')
            news_page['title'] = article.h1.text.strip()
            article_content = article.find('div', class_='text')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article)
        elif category == 'sports':
            article = soup.find('div', class_='news_content')
            news_page['title'] = article.h1.text.strip()
            article_content = article.find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article)
        elif category == 'talk':
            article = soup.find('div', class_='conbox')
            news_page['title'] = article.h1.text.strip()
            article_content = article.find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article)
        elif category == 'istyle':
            article_title = soup.find('div', class_='caption')
            news_page['title'] = article_title.h2.text.strip()
            article_content = soup.find('article').find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article_title)
        elif category == '3c':
            article = soup.find('div', class_='conbox')
            news_page['title'] = article.h1.text.strip()
            article_content = article.find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article)
        elif category == 'market':
            article = soup.find('div', class_='whitecon articlebody boxTitle')
            news_page['title'] = article.h1.find('div', class_='boxText').text.strip()
            article_content = article.find('div', class_='text')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article_content)
        elif category == 'auto':
            article_title = soup.find('h1', class_='h1tt')
            news_page['title'] = article_title.text.strip()
            article_content = soup.find('div', itemprop='articleBody')
            p_tags = article_content.find_all('p',recursive=False)
            news_page['body'] = "\n".join([p.text for p in p_tags])
            news_page['publish_time'] = self.fetch_publish_time(category, article_content)
        return news_page

    def fetch_publish_time(self, category, soup):
        publish_time = ''
        if category == 'news':
            publish_time = soup.find('span', class_='viewtime').text
        elif category == 'ent':
            publish_time = soup.find('div', class_='date').text
        elif category == 'ec':
            publish_time = soup.find('span', class_='time').text
        elif category == 'sports':
            publish_time = soup.find('div', class_='c_time').text
        elif category == 'talk':
            publish_time = soup.find('div', class_='mobile_none').text
        elif category == 'istyle':
            time_string = soup.find('div', class_='label-date').text
            publish_time = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string, '%b. %d %Y %H:%M:%S'))
        elif category == '3c':
            publish_time = soup.find('div', class_='writer').select('span')[1].text
        elif category == 'market':
            publish_time = soup.find('span', class_='date1').text
        elif category == 'auto':
            publish_time = soup.find('span', class_='h1dt').text
        return publish_time
    
    def extract_type(self, url):
        hostname = urlparse(url).hostname
        page_type = hostname.split('.')[0]
        return page_type
    
    
    def run(self):
        """
        程式進入點
        """
        # crawl_category = ['news', 'ent', 'ec', 'sports']
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)
        for row in crawl_list:
            redirected_url, html = self.fetch_html(row['url'])
            print(row['url'])
            print(redirected_url)
            page_type = self.extract_type(redirected_url)
            # if page_type not in crawl_category:
            #     continue
            soup = BeautifulSoup(html, 'html.parser')
            news_page = self.fetch_news_content(page_type, soup)
            print(news_page)
            news_page['list_id'] = row['id']
            news_page['url'] = row['url']
            news_page['url_md5'] = row['url_md5']
            news_page['redirected_url'] = redirected_url
            news_page['source_id'] = source_id
            news_page['image'] = 0
            news_page['video'] = 0

            self.floodfire_storage.insert_page(news_page)
            # 更新爬抓次數記錄
            self.floodfire_storage.update_list_crawlercount(row['url_md5'])
            sleep(2)

        # redirected_url, html = self.fetch_html('http://auto.ltn.com.tw/news/10906/3')
        # page_type = self.extract_type(redirected_url)
        # soup = BeautifulSoup(html, 'html.parser')
        # news_page = self.fetch_news_content(page_type, soup)
        # print(news_page)