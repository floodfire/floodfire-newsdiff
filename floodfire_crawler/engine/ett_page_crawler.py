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
from floodfire_crawler.service.diff import FloodfireDiff

class EttPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "ett"
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

        # 內容所在位置
        story = soup.find('div',{'class':'story'}).select('p')
            #有些文章會多包一層<p>
        story = [x for x in story if x.p==None]
            #有些又少包一個層<p>
        pure_story = re.sub('\n+','\n',('\n'.join([x.text for x in story])).\
            replace('\r\n','\n').replace('\n\r','\n')).split('\n')


        # --- 取出標題 ---
        page['title'] = soup.h1.text.replace("　", " ").replace("\u200b","")

        # --- 取出內文 ---
        page['body'] = ('\n').join([x for x in pure_story if \
                len([p for p in ['▲', '▼', '文／'] if p in x])==0 and len(x)>0\
                and not (x.find('記者')>=0 and x.find('報導')>=0 and len(x)<20)\
                and not (x.find('中心')>=0 and x.find('報導')>=0 and len(x)<20)])


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
        #authors
        authors = [x for x in pure_story \
                if(len(x)<20) and\
                ((x.find('記者')>=0 and x.find('報導')>=0)\
                or (x.find('中心')>=0 and x.find('報導')>=0)\
                or x.find('文／')>=0)]
        authors = [author[0:author.find('／')].replace(' ','').replace('記者','') \
                if author.find('報導')>0 else\
                author[(author.find('／')+1):].replace(' ','').replace('記者','')
                for author in authors]
        page['authors'] = authors
        
        # --- 取出圖片數 ---
        pic_urls_index = [i for i in range(0, len(story)) if story[i].img != None]
        pic_list = list()
        for i in pic_urls_index:
            if((i-1)>=0 and story[i-1].text.find('▼')>=0):
                pic_list.append({'url':"https:"+story[i].img['src'], 'desc': story[i-1].text})
            elif((i+1)<len(story) and story[i+1].text.find('▲')>=0):
                pic_list.append({'url':"https:"+story[i].img['src'], 'desc': story[i+1].text})  
            else:
                pic_list.append({'url':"https:"+story[i].img['src'], 'desc': ""})

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
        video_urls_index = [i for i in range(0, len(story)) if story[i].iframe != None]
        video_list = list()
        for i in video_urls_index:
            if(i-1>=0 and story[i-1].text.find('▼')>=0):
                video_list.append({'url':story[i].iframe['src'], 'desc': story[i-1].text})
            elif(i+1<len(story) and story[i+1].text.find('▲')>=0):
                video_list.append({'url':story[i].iframe['src'], 'desc': story[i+1].text})  
            else:
                video_list.append({'url':story[i].iframe['src'], 'desc': ""})      

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
        time_text = re.findall('\d+', soup.time.text )
        date = '-'.join(time_text[0:3])
        if(len(time_text[3:])==3):
            return(date+" "+':'.join(time_text[3:]))
        elif(len(time_text[3:])==2):
            return(date+" "+':'.join(time_text[3:]) + ":00")
        elif(len(time_text[3:])==1):
            return(date+" "+':'.join(time_text[3:]) + ":00:00")
        else:
            return(date+" "+'00:00:00')
    
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
        version = 1
        table_name = None
        diff_vals = (version, None, None)
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
                if status_code == requests.codes.ok:
                    print('crawling... id: {}'.format(row['id']))

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw['list_id'] = row['id']
                        news_page_raw['url'] = row['url']
                        news_page_raw['url_md5'] = row['url_md5']
                        news_page_raw['page_content'] =  self.compress_html(html_content['html'])
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print('Save ' + str(row['id']) + ' page Raw.')

                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    news_page = self.fetch_news_content(soup)
                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id
                    ######Diff#######
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
