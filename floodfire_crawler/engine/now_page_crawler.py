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


class NowPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "now"
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            resp_content = {
                'redirected_url': response.url,  # 取得最後 redirect 之後的真實網址
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

        page = {}

        # --- 取出標題 ---
        page['title'] = soup.find('h1', class_='entry-title').text

        # --- 取出內文 ---
        page['body'] = "\n".join([p.text for p in soup.find('span', {"itemprop": 'articleBody'}).findAll('p')])

        # --- 取出發布時間 ---
        page['publish_time'] = self.fetch_publish_time(soup)

        # --- 取出關鍵字 ---
        # keywords=
        page['keywords'] = [a.text for a in soup.find('div', class_='td-post-source-tags').findAll('a')]

        # --- 取出記者 ---
        # authors
        page['authors'] = [soup.find('div', class_='td-post-author-name').text.strip('\n')[:-2].strip(' ')]

        # --- 取出圖片數 ---
        image = soup.find('div', class_='td-post-content').findAll('figure')
        page['image'] = len(image)

        page['visual_contents'] = list()
        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = [{
            'type': 1,
            'visual_src': i.img['src'] if i.noscript is None else i.noscript.img['src'],
            'caption': i.figcaption.text if i.figcaption is not None else "None"
        }for i in image]

        # --- 取出影片數 ---

        video = soup.find('span', {"itemprop": 'articleBody'}).findAll(
            'p')[-1].noscript.iframe
        if video:
            page['video'] = 1
            # -- 取出視覺資料連結（影片） ---
            page['visual_contents'].append({
                'type': 2,
                'visual_src': video['src'],
                'caption': None
            })
        else:
            page['video'] = 0

        return page

    def fetch_publish_time(self, soup):
        # time = soup.find('div', class_='content_date').text.lstrip()[3:].rstrip()
        # news_time = strftime('%Y-%m-%d %H:%M:%S', strptime(time, '%Y.%m.%d | %H:%M'))
        return soup.find('time').text

    def compress_html(self, page_html):
        """
        壓縮原始的 HTML

        Keyword arguments:
            page_html (string) -- 原始 html
        """
        # minhtml = re.sub('>\s*<', '><', page_html, 0, re.M)
        minhtml = htmlmin.minify(page_html, remove_empty_space=True)
        return minhtml

    def run(self, page_raw=False, page_diff=False, page_visual=False):
        """
        程式進入點
        """
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)
        # log 起始訊息
        start_msg = 'Start crawling ' + \
            str(len(crawl_list)) + ' ' + self.code_name + '-news lists.'
        if page_raw:
            start_msg += ' --with save RAW'
        if page_visual:
            start_msg += ' --with save VISUAL_LINK'
        self.logme.info(start_msg)
        # 本次的爬抓計數
        crawl_count = 0

        for row in crawl_list:
            try:
                status_code, html_content = self.fetch_html(row['url'])
                if status_code == requests.codes.ok:
                    print('crawling... id: {}'.format(row['id']))

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw['list_id'] = row['id']
                        news_page_raw['url'] = row['url']
                        news_page_raw['url_md5'] = row['url_md5']
                        news_page_raw['page_content'] = self.compress_html(
                            html_content['html'])
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print('Save ' + str(row['id']) + ' page Raw.')

                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    news_page = self.fetch_news_content(soup)
                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id
                    if self.floodfire_storage.insert_page(news_page):
                        # 更新爬抓次數記錄
                        self.floodfire_storage.update_list_crawlercount(
                            row['url_md5'])
                        # 本次爬抓計數+1
                        crawl_count += 1
                    else:
                        # 更新錯誤次數記錄
                        self.floodfire_storage.update_list_errorcount(
                            row['url_md5'])

                    # 儲存圖片或影像資訊
                    if page_visual and len(news_page['visual_contents']) > 0:
                        for vistual_row in news_page['visual_contents']:
                            vistual_row['list_id'] = row['id']
                            vistual_row['url_md5'] = row['url_md5']
                            self.floodfire_storage.insert_visual_link(vistual_row)

                    # 隨機睡 2~6 秒再進入下一筆抓取
                    sleep(randint(2, 6))
                else:
                    # get 網頁失敗的時候更新 error count
                    self.floodfire_storage.update_list_errorcount(row['url_md5'])
            except Exception as e:
                self.logme.exception('error: list-' + str(row['id']) + ' ' + str(e.args))
                # 更新錯誤次數記錄
                self.floodfire_storage.update_list_errorcount(row['url_md5'])
                pass
        self.logme.info('Crawled ' + str(crawl_count) + ' ' + self.code_name + '-news lists.')
