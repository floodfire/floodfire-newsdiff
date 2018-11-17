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

class UdnPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "udn"
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

        page = {}

        # --- 取出標題 ---
        title = soup.h1.text.replace("　", " ").replace("\u200b","")
        page['title'] = title

        # --- 取出內文 ---
        sub_content = [] if soup.find('div', id = 'story_body_content') == None \
        else [x.text.strip() for x in soup.find('div', id = 'story_body_content').select('p') \
            if x.div==None and x.blockquote == None and len(x.text.strip())>0]

        sub_content2 = [] if soup.find('main') == None \
        else [x.text.strip() for x in soup.find('main').select('p') \
            if x.div==None and x.blockquote == None and len(x.text.strip())>0]

        content = sub_content + sub_content2 

        page['body'] = ('\n').join(content)

        # --- 取出發布時間 ---
        page['publish_time'] = self.fetch_publish_time(soup)
        
        # --- 取出關鍵字 ---
        #keywords
        tags = [] if soup.find('div',{'class','tag'}) == None \
        else [x.text for x in soup.find('div',{'class','tag'}).select('a')]
        tags2 = [] if soup.find('p',{'class','tag'}) == None \
        else [x.text for x in soup.find('p',{'class','tag'}).select('a')]  
        page['keywords'] = tags + tags2
        
        # --- 取出記者 ---
        #author
        author_sub = '' if soup.find('div',{'class', 'story_bady_info_author'}) == None \
                        or soup.find('div',{'class', 'story_bady_info_author'}).a == None \
                    else soup.find('div',{'class', 'story_bady_info_author'}).a.text
        if soup.find('div',{'class', 'story_bady_info_author'}) != None and\
           author_sub == '':
            author_sub = str(soup.find('div',{'class', 'story_bady_info_author'}).span.next_sibling).split(' ')[0]
        author_sub2 = '' if soup.find('div',{'class', 'shareBar__info--author'}) == None \
                or soup.find('div',{'class', 'shareBar__info--author'}).span == None \
            else str(soup.find('div', {'class', 'shareBar__info--author'}).span.next_sibling)
        author = author_sub+author_sub2
        page['authors'] = author
        
        # --- 取出圖片數 ---
        img_raws = soup.select('figure img')
        pic_list = list()
        if(len(img_raws)>0):
            for img_raw in img_raws:
                pic_list.append({'url':img_raw['src'], 'desc':img_raw['alt']})
        page['image'] = len(pic_list)

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        for img in pic_list:
            page['visual_contents'].append({
                    'type': 1,
                    'visual_src': img['url'],
                    'caption': img['desc']
                })

        # --- 取出影片數 ---
        video_raws = soup.find('div', {'class': 'video-container'})
        video_list = list()
        if(video_raws !=None):
            for video_raw in video_raws.select('iframe'):
                video_list.append({'url':video_raw['src'], 'desc':title})


        page['video'] = len(video_list)
        
        # -- 取出視覺資料連結（影片） ---
        for video in video_list:
            page['visual_contents'].append({
                    'type': 2,
                    'visual_src': video['url'],
                    'caption': video['desc']
                })
        return page   
    
    def fetch_publish_time(self, soup):
        time_sub = '' if soup.find('div',{'class', 'story_bady_info_author'}) == None \
                  else soup.find('div',{'class', 'story_bady_info_author'}).span.text+":00"
        time_sub2 = '' if soup.find('div',{'class', 'shareBar__info--author'}) == None \
                  else soup.find('div',{'class', 'shareBar__info--author'}).span.text
        time = time_sub + time_sub2
        return(time)
    
    def compress_html(self, page_html):
        """
        壓縮原始的 HTML

        Keyword arguments:
            page_html (string) -- 原始 html
        """
        # minhtml = re.sub('>\s*<', '><', page_html, 0, re.M)
        minhtml = htmlmin.minify(page_html, remove_empty_space=True)
        return minhtml
    
    def run(self, page_raw=False, page_diff=False, page_visual = False):
        """
        程式進入點
        """
        # crawl_category = ['news', 'ent', 'ec', 'sports']
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)
        # log 起始訊息
        start_msg = 'Start crawling ' + str(len(crawl_list)) + ' ' + self.code_name + '-news lists.'
        if page_raw:
            start_msg += ' --with save RAW'
        self.logme.info(start_msg)
        # 本次的爬抓計數
        crawl_count = 0

        for row in crawl_list:
            try:
                status_code, html_content = self.fetch_html(row['url'])
                # test related pages
                # url = 'https://udn.com/news/story/7332/3477556'
                # status_code, html_content = self.fetch_html(url)

                if status_code == requests.codes.ok:
                    print('crawling... id: {}'.format(row['id']))

                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    news_page = self.fetch_news_content(soup)
                    #miss while redirect
                    publish_time = news_page['publish_time']
                    #if there is redirection
                    if('window.location.href' in news_page['body']):
                        print('redirecting... id: {} ...skip'.format(row['id']))
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])
                        continue
                        # redirect_url = re.findall('https?://(?:[-\w/.]|(?:%[\da-fA-F]{2}))+', news_page['body'])[0]
                        # status_code, html_content = self.fetch_html(redirect_url)
                        # if status_code == requests.codes.ok:
                        #     print('redirecting... id: {}'.format(row['id']))
                        #     print(redirect_url)
                        #     soup = BeautifulSoup(html_content['html'], 'html.parser')
                        #     news_page = self.fetch_news_content(soup)
                        #     #put back normal time
                        #     if(not news_page['publish_time'][0].isdigit()):
                        #         news_page['publish_time'] = publish_time
                        #     #update redirected_url
                        #     html_content['redirected_url'] = redirect_url
                        # else:
                        #         # get 網頁失敗的時候更新 error count
                        #     self.floodfire_storage.update_list_errorcount(row['url_md5'])

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw['list_id'] = row['id']
                        news_page_raw['url'] = row['url']
                        news_page_raw['url_md5'] = row['url_md5']
                        news_page_raw['page_content'] =  self.compress_html(html_content['html'])
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print('Save ' + str(row['id']) + ' page Raw.')

                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id
                    if self.floodfire_storage.insert_page(news_page):
                        # 更新爬抓次數記錄
                        self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                        # 本次爬抓計數+1
                        crawl_count += 1
                    else:
                        # 更新錯誤次數記錄
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])

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
