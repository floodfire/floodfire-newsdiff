#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage

class ApdPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "apd"
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
        #延伸閱讀的前綴語句
        tail_list = ['看了這則新聞的人','想知道更多']
        fake_img_list = ['//img.appledaily.com.tw/images/NextDigital/logo_NextMedia_m.png']
        
        page = {}
        for br in soup.find_all("br"):
            br.replace_with("\n")
        
        # --- 取出標題 ---
        page['title'] = soup.hgroup.h1.text.strip().replace("　", " ").replace("\u200b","")

        # --- 取出內文 ---
        content = soup.select('div p')[0].text.replace("　"," ").replace("\u200b","")
        tails = [content.find(a_tail) for a_tail in tail_list if content.find(a_tail)>0]
        news_content = content if len(tails)==0 else content[0:min(tails)]
        page['body'] = news_content

        # --- 取出發布時間 ---
        page['publish_time'] = self.fetch_publish_time(soup)
        
        # --- 取出關鍵字 ---
        #keywords
        keys = [x.text for x in soup.select('h3 a')]
        page['keywords'] = keys
        
        # --- 取出記者 ---
        #authors
        brackets = re.findall('(?:（|\()(.*?)(?:）|\))', news_content)
        split_publishers = re.findall("\w+",(', '.join([bracket for bracket in brackets if bracket.find("報導") > 0])))
        publishers = list(set([x for x in split_publishers if len(re.findall("報導",x))==0]))
        page['authors'] = publishers
        
        # --- 取出圖片數 ---
        #has_image
        cover_img = soup.findAll('div',{'class':'ndAritcle_headPic'})
        foot_img = [y['src'] for y in soup.select('figure img') if y['src'] not in fake_img_list]
        page['image'] = (len(foot_img) + len(cover_img))
        #has_video
        
        # --- 取出影片數 ---        
        has_video = 1 if soup.find('div',{'id':'videobox'}) else 0
        page['video'] = has_video
        
        """
        #可以擷取影片網址以及影片截圖
        video_box = soup.find('div',{'id':'videobox'})

        re.findall('https?://(?:[-\w./])+.(?:mp4)', video_box.select('script')[-1].text)[0]
        
        re.findall('https?://(?:[-\w./])+.(?:jpg|gif|png)', video_box.select('script')[-1].text)[0]

        """
        return page   
    
    def fetch_publish_time(self, soup):
        time = soup.select('.ndArticle_creat')[0].text.strip()
        news_time = strftime('%Y-%m-%d %H:%M:%S', strptime(time[time.find('：')+1:], '%Y/%m/%d %H:%M'))
        return(news_time)
    
    def run(self):
        """
        程式進入點
        """
        # crawl_category = ['news', 'ent', 'ec', 'sports']
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        crawl_list = self.floodfire_storage.get_crawllist(source_id)
        self.logme.info('Start crawling ' + str(len(crawl_list)) + ' ' + self.code_name + '-news lists.')
        # 本次的爬抓計數
        crawl_count = 0

        for row in crawl_list:
            try:
                status_code, html_content = self.fetch_html(row['url'])
                print('crawling... id: {}'.format(row['id']))
                if status_code == requests.codes.ok:
                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    if(soup.contents[0]!='html'):
                        self.floodfire_storage.update_list_errorcount(row['url_md5'])
                        continue
                    news_page = self.fetch_news_content(soup)
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
