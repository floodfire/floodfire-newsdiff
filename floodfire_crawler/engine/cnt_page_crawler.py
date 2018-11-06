#!/usr/bin/env python3

import requests
import re
import htmlmin
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class CntPageCrawler(BasePageCrawler):
    
    def __init__(self, config, logme):
        self.code_name = "cnt"
        self.floodfire_storage = FloodfireStorage(config)
        self.logme = logme
    
    def fetch_html(self, url):
        """
        取出網頁 HTML 原始碼

        Keyword arguments:
            url (string) -- 抓取的網頁網址
        """
        try:
            headers = {
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }
            response = requests.get(url, headers=headers, timeout=15)
            resp_content = {
                'redirected_url': response.url, # 取得最後 redirect 之後的真實網址
                'html': response.text
            }
        except requests.exceptions.HTTPError as err:
            msg = "HTTP exception error: {}".format(err.args[1])
            self.logme.error(msg)
            return 0, msg
        except requests.exceptions.RequestException as e:
            msg = "Exception error {}".format(e.args[1])
            self.logme.error(msg)
            return 0, msg

        return response.status_code, resp_content

    def fetch_news_content(self, soup):
        """
        傳回新聞頁面中的內容

        keyward arguments:
            soup (object) -- beautifulsoup object
        """
        page = dict()
        # --- 取出標題 ---
        page['title'] = soup.select('div#bigpicbox h1#h1')[0].text.strip()
        # --- 取出內文 ---
        article_content = soup.select('article.arttext')[0]
        p_tags = article_content.find_all('p')
        page['body'] = "\n".join([p.text for p in p_tags])

        # --- 取出發布時間 ---
        page['publish_time'] = self.fetch_publish_time(article_content)
        
        # --- 取出記者 ---
        page['authors'] = article_content.find('div', class_='rp_name').find('cite').text.strip()
        
        # --- 取出關鍵字 ---
        keywords = soup.find('meta', attrs={'name':'news_keywords'})
        page['keywords'] = keywords['content'].strip()

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        if soup.find('div', class_='picbox1'):
            cover_img=soup.find('div', class_='picbox1')
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': 'https:' + cover_img.find('img')['src'],
                    'caption': cover_img.find('a')['title']
                })
        imgs = article_content.find_all('div', class_='picbox')
        for img in imgs:
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': 'https:' + img.find('img')['src'],
                    'caption': img.find('span').text.strip()
                })

        # -- 取出視覺資料連結（影片） ---
        if soup.find('div', class_='video'):
            video = soup.find('div', class_='video')
            if video.find('div', id='jw-container'):
                print(video.find('div', id='jw-container'))
                # page['visual_contents'].append(
                # {
                #     'type': 2,
                #     'visual_src': video.find('div', id='jw-container').find('iframe')['src'],
                #     'caption': video.find('div', id='jw-container').find('figcaption').text.strip()
                # })
        print(soup.find_all('div', class_='video_iframe'))
        
        # print(page)

    def fetch_publish_time(self, soup):
        """
        取得新聞發佈時間

        keyward arguments:
            soup (object) -- beautifulsoup object
        """
        time = soup.find('time').text.strip()
        news_time = strftime('%Y-%m-%d %H:%M:%S', strptime(time, '%Y年%m月%d日 %H:%M'))
        return news_time

    def run(self, page_raw=False, page_diff=False, page_visual=False):
        """
        程式進入點
        """
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)

        # log 起始訊息
        start_msg = 'Start crawling ' + str(len(crawl_list)) + ' ' + self.code_name + '-news lists.'
        if page_raw:
            start_msg += ' --with save RAW'
        if page_visual:
            start_msg += ' --with save VISUAL_LINK'
        self.logme.info(start_msg)

        # 本次的爬抓計數
        crawl_count = 0

        # 單頁測試
        status_code, html_content = self.fetch_html('https://www.chinatimes.com/realtimenews/20181106002002-260407')
        if status_code == requests.codes.ok:
            # page_type = self.extract_type(html_content['redirected_url'])
            soup = BeautifulSoup(html_content['html'], 'html.parser')
            news_page = self.fetch_news_content(soup)
            # print(news_page)
            # # 儲存圖片或影像資訊
            # if page_visual and len(news_page['visual_contents']) > 0:
            #     for vistual_row in news_page['visual_contents']:
            #         vistual_row['list_id'] = 100
            #         vistual_row['url_md5'] = '60420fb89e8141139755f7f99ddf8e4e'
            #         self.floodfire_storage.insert_visual_link(vistual_row)