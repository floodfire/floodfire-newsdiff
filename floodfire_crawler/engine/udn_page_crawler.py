#!/usr/bin/env python3

import requests
import re
import htmlmin
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
from floodfire_crawler.service.diff import FloodfireDiff

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
        if soup.find('h1', {'class', 'story_art_title'}) is None:
            title = soup.h1.text.replace("　", " ").replace("\u200b","")
        else:
            title = soup.find('h1', {'class', 'story_art_title'}).text
        page['title'] = title

        # --- 取出發布時間 ---
        if soup.find('div',{'class', 'story_bady_info_author'}) is not None:
            if soup.find('div',{'class', 'story_bady_info_author'}).time is not None:
                page['publish_time'] = soup.find('div',{'class', 'story_bady_info_author'}).time['datetime'] + ' 00:00'
            else:
                page['publish_time'] = soup.find('div',{'class', 'story_bady_info_author'}).span.text
        else:
            if soup.find('div',{'class', 'shareBar'}) is not None:
                page['publish_time'] = soup.find('div',{'class', 'shareBar'}).span.text
            elif soup.find('div',{'class', 'article-info'}) is not None:
                page['publish_time'] = soup.find('div', {'class', 'article-info'}).text
            else:
                page['publish_time'] = soup.find('section', {'class', 'authors'}).time.text+':00'

        # --- 取出關鍵字 ---
        #keywords
        tag_area = soup.find(id='story_tags')
        if tag_area is not None:
            page['keywords'] = [x.text for x in soup.find(id='story_tags').find_all('a')]
        elif len(soup.find_all('a', {'class', 'tag-name'})) > 0:
            page['keywords'] = [x.text for x in soup.find_all('a', {'class', 'tag-name'})]
        elif len(soup.find_all('a', {'class', 'btn-keyword'}))>0:
            page['keywords'] = [x.text for x in soup.find_all('a', {'class', 'btn-keyword'})]
        else:
                page['keywords'] = []
        
        # --- 取出記者 ---
        #author
        author_list = []
        author_area = soup.find('div',{'class', 'story_bady_info_author'})
        if author_area is not None:
            if author_area.a is not None:
                author_list.append(author_area.a.text)
            else:
                author_list.append(author_area.find(text=True, recursive=False).split(' ')[0])
        else:
            if soup.find('div',{'class', 'shareBar__info--author'}) is not None:
                author_list.append(soup.find('div',{'class', 'shareBar__info--author'}).find(text=True, recursive=False).split(' ')[-1])
            elif soup.find('a', {'class', 'article-info'}) is not None:
                author_list.append(soup.find('a', {'class', 'article-info'}).text.split(' ')[-1])
            else:
                author_section = soup.find('section', {'class', 'authors'}).span
                if (author_section.a is not None):
                    author_list.append(author_section.a.text)
                else:
                    author_list.append(author_section.text)

        page['authors']=author_list

        # --- 取出圖片數 ---
        img_raws = soup.select('figure')
        pic_list = list()
        if(len(img_raws)>0):
            for img_raw in img_raws:
                if img_raw.find('div', {'class', 'imgbox'}) is None:
                    if img_raw.a is not None:
                        pic_list.append({'url':img_raw.a['href'], 'desc':img_raw.find('figcaption').text})
                    elif img_raw.img is not None:
                        img_url = img_raw.img['src'] if img_raw.img.has_attr('src') else img_raw.img['data-src']
                        img_desc = img_raw.img['title'] if img_raw.img.has_attr('title') else img_raw.text
                        pic_list.append({'url':img_url, 'desc':img_desc})
                    
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
        video_raws = soup.find_all('div', {'class': 'video-container'})
        video_list = list()
        if(video_raws !=None):
            for video_raw in video_raws:
                if video_raw.iframe.has_attr('src'):
                    video_url = video_raw.iframe['src']
                else:
                    video_url = None
                if video_raw.iframe.has_attr('desc'):
                    video_desc = video_raw.iframe['desc']
                else:
                    video_desc = None
                video_list.append({'url':video_url, 'title':video_desc})

        page['video'] = len(video_list)
        
        # -- 取出視覺資料連結（影片） ---
        for video in video_list:
            page['visual_contents'].append({
                    'type': 2,
                    'visual_src': video['url'],
                    'caption': video['title']
                })

        # --- 取出內文 ---
        while soup.find('figcaption') != None:
            soup.figcaption.decompose()
        while soup.find('figure') != None:
            soup.figure.decompose()
        while soup.find('blockquote') != None:
            soup.blockquote.decompose()
        # 去除廣告
        while soup.find("div", "modal") !=None:
            soup.find("div", "modal").decompose()
        # 去除推薦文章
        while soup.find("div", "story-list__text") !=None:
            soup.find("div", "story-list__text").decompose()
        # 如果有轉址
        content_area = soup.find_all('p')
        if 'window.location.href' in content_area[0].text:
            page['body'] = content_area[0].text
        else:
            contents = [x.text for x in content_area if x.text != '' and x.text!=' ' and x.text!='\n' and x.p is None and x.script is None]
            # 如果內文只有一張圖
            if(len(contents)==0):
                page['body'] = ''
                return page
            if(contents[0][0]==' '):
                contents[0] = contents[0][1:]
            page['body'] = ('\n').join(contents)

        return page   

    def fetch_publish_time(self, soup):
        pass
    
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
        ######Diff#######
        if page_diff:
            diff_obj = FloodfireDiff()
        else:
            diff_obj = None
        ######Diff#######
        crawl_list = self.floodfire_storage.get_crawllist(source_id, page_diff, diff_obj)
        # log 起始訊息
        start_msg = 'Start crawling ' + str(len(crawl_list)) + ' ' + self.code_name + '-news lists.'
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
                print(row['url'])
                if status_code == requests.codes.ok:
                    print('crawling... id: {}'.format(row['id']))
                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    news_page = self.fetch_news_content(soup)
                    
                    #miss while redirect, put back later
                    publish_time = news_page['publish_time']

                    #if there is redirection
                    if('window.location.href' in news_page['body']):
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])
                        redirect_url = re.findall('https?://(?:[-\w/.]|(?:%[\da-fA-F]{2}))+', news_page['body'])[0]
                        status_code, html_content = self.fetch_html(redirect_url)
                        if status_code == requests.codes.ok:
                            print('redirecting... id: {}'.format(row['id']))
                            print(redirect_url)
                            soup = BeautifulSoup(html_content['html'], 'html.parser')
                            news_page = self.fetch_news_content(soup)
                            #put back normal time
                            if(not news_page['publish_time'][0].isdigit()):
                                news_page['publish_time'] = publish_time
                            #update redirected_url
                            html_content['redirected_url'] = redirect_url
                        else:
                            # get 網頁失敗的時候更新 error count
                            self.floodfire_storage.update_list_errorcount(row['url_md5'])

                    # 特例：台灣醒報
                    if (news_page['authors'][0] == '台灣醒報'):
                        print('台灣醒報，跳過')
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])
                        sleep(randint(2, 6))
                        continue

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
                    news_page['publish_time'] = str(datetime.strptime(news_page['publish_time'][:16], '%Y-%m-%d %H:%M'))
                    ######Diff#######
                    version = 1
                    table_name = None
                    diff_vals = (version, None, None)
                    if page_diff:
                        last_page, table_name = self.floodfire_storage.get_last_page(news_page['url_md5'],
                                                                                     news_page['publish_time'],
                                                                                     diff_obj.compared_cols)
                        if last_page != None:
                            diff_col_list = diff_obj.page_diff(news_page, last_page)
                            if diff_col_list is None:
                                # 有上一筆，但沒有不同，更新爬抓次數，不儲存
                                print('has last, no diff')
                                crawl_count += 1 
                                self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                                continue
                            else:
                                # 出現Diff，儲存
                                version = last_page['version'] + 1
                                last_page_id = last_page['id']
                                diff_cols = ','.join(diff_col_list)
                                diff_vals = (version, last_page_id, diff_cols)
                    ######Diff#######
                    print(diff_vals)
                    if self.floodfire_storage.insert_page(news_page, table_name, diff_vals):
                        # 更新爬抓次數記錄
                        self.floodfire_storage.update_list_crawlercount(row['url_md5'])
                        self.floodfire_storage.update_list_versioncount(row['url_md5'])                        
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
                            self.floodfire_storage.insert_visual_link(vistual_row, version)
                    
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
