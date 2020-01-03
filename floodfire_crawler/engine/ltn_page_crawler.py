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

class LtnPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "ltn"
        self.regex_pattern = re.compile(r"[［〔]記者(\w*)／\w*[〕］]")
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

    def __news_category(self, soup):
        """
        取出 news 類別需要的資料內容
        """
        page = dict()
        page['title'] = soup.h1.text.strip()
        article_content = [x.text for x in soup.find('div', class_='text').find_all('p', recursive = False) if x.text!='' and x.text.find('\u3000\n')<0 and x.text.find('往下閱讀')<0]
        page['body'] = "\n".join(article_content)
        page['publish_time'] = re.sub(r'\n[ ]+', '', soup.find('span', class_='time').text+ ':00')
        page['keywords'] = soup.find('meta', {'name' : 'keywords'})['content'].split(',')
        page['authors'] = self.extract_author(page['body'])

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()

        imgs = soup.find('div', class_='text').find_all('img')
        for img in imgs:
            if(img['src'].find('http')>-1):
                page['visual_contents'].append(
                    {
                        'type': 1,
                        'visual_src': img['src'],
                        'caption': img['title']
                    })
        
        return page

    def __ent_category(self, soup):
        """
        取出 ent 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', itemprop='articleBody')
        page['title'] = article.h1.text.strip()
        p_tags = article.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        time_string = soup.find('meta', attrs={'name':'pubdate'})
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string['content'][:-6], '%Y-%m-%dT%H:%M:%S'))

        # -- 娛樂新聞沒有關鍵字
        page['keywords'] = list()
        # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
        if soup.find('meta', attr={'name':'keywords'}):
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出記者 ---
        page['authors'] = self.extract_author(page['body'])

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()

        visuals = article.find_all('span', class_='ph_b ph_d1 tb-c')
        
        for visual in visuals:
            img = visual.find('img')
            caption = visual.find('span', class_='ph_d').text.strip()
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['data-original'],
                    'caption': caption
                })
        return page

    def __ec_category(self, soup):
        """
        取出 ec 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='whitecon boxTitle')
        page['title'] = article.h1.text.strip()
        page['body'] = "\n".join([x.text for x in soup.find_all('p') if x.text != '' and x.text!='爆' and x.text.find('\u3000\n')<0 and x.text.find('加入自由電子')<0])
        page['publish_time'] = article.find('span', class_='time').text + ':00'

        # --- 取出關鍵字 ---
        page['keywords'] = (soup.find('meta', {'name':'keywords'})['content'])

        # -- 取出記者 ---
        page['authors'] = self.extract_author(page['body'])

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = soup.find_all('span', class_='ph_b ph_d1')
        for visual in visuals:
            img = visual.find('img')
            if visual.find('span', class_='ph_d') is not None:
                caption = visual.find('span', class_='ph_d').text.strip()
            else:
                caption = ''
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
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
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        page['publish_time'] = article.find('div', class_='c_time').text + ':00'

        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if article.find('div', class_='keyword boxTitle'):
            keywords = article.find('div', class_='keyword boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())
        
        # -- 取出記者 ---
        page['authors'] = self.extract_author(page['body'])
        
        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = article_content.find_all('span', class_='ph_b ph_d1')
        for visual in visuals:
            img = visual.find('img')
            caption = visual.find('span', class_='ph_d').text.strip()
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
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
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        
        # 有無作者資訊會影響出現的時間區段
        if article.find('div', class_='mobile_none'):
            page['publish_time'] = article.find('div', class_='mobile_none').text + ':00'
        elif article.find('div', class_='writer_date'):
            page['publish_time'] = article.find('div', class_='writer_date').text + ':00'

        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if article.find('div', class_='kwtab boxTitle'):
            keywords = article.find('div', class_='kwtab boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出文章作者 ---
        if article.find('div', class_='writer boxTitle'):
            page['authors'] = article.find('div', class_='writer boxTitle').find('a')['data-desc']
        else:
            page['authors'] = list()

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = article_content.find_all('span', class_='ph_b ph_d1')
        for visual in visuals:
            img = visual.find('img')
            caption = visual.find('span', class_='ph_d').text.strip()
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
        return page

    def __istyle_category(self, soup):
        """
        取出 istyle 類別需要的資料內容
        """
        page = dict()
        article_title = soup.find('div', class_='caption')
        page['title'] = article_title.h2.text.strip()
        article_content = soup.find('article').find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p', recursive=False)
        page['body'] = "\n".join([x.text for x in p_tags if x.text!='' and x.text.find('\u3000\n')<0 and x.text.find('往下閱讀')<0 and x.text.find('延伸閱讀')<0 and x.img == None and 'class' not in x.attrs and 'style' not in x.attrs])

        time_string = article_title.find('div', class_='label-date').text
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string, '%b. %d %Y %H:%M:%S'))

        # --- 取出關鍵字 ---
        # 2018-11-13 發現時尚網頁改版，沒有關鍵字區段
        page['keywords'] = list()
        if soup.find('article').find('section', class_='tag boxTitle'):
            keywords = soup.find('article').find('section', class_='tag boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出記者 ---
        author = article_title.find('p', class_='auther').find('span').text.strip()
        page['authors'] = re.findall(r'文／記者(\w*)', author)

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = article_content.find_all('span', class_=['ph_b', 'ph_d1'])
        for visual in visuals:
            img = visual.find('img')
            if (visual.find('span', class_='ph_d') != None):
                caption = visual.find('span', class_='ph_d').text.strip()
            else:
                caption = ''
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
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
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        page['publish_time'] =  article.find('div', class_='writer').select('span')[1].text + ':00'
        
        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if article.find('div', class_='contab boxTitle boxText'):
            keywords = article.find('div', class_='contab boxTitle boxText').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出記者 ---
        author = article.find('div', class_='writer').find('span').text.strip()
        page['authors'] = re.findall(r'文／記者(\w*)', author)
        
        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()

        visuals = article_content.find_all('span', class_='ph_b ph_d1 ')
        for visual in visuals:
            img = visual.find('img')
            caption = visual.find('span', class_='ph_d').text.strip()
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
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
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
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
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        page['publish_time'] = article_content.find('span', class_='h1dt').text + ':00'

        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if soup.find('div', class_='kw2 boxTitle'):
            keywords = soup.find('div', class_='kw2 boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出記者 ---
        author = article_content.find('span', class_='writer').text.strip()
        page['authors'] = re.findall(r'文／記者(\w*)', author)
        
        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = article_content.find_all('span', class_=['ph_b', 'ph_d1'])
        for visual in visuals:
            img = visual.find('img')
            if visual.find('span', class_='ph_d'):
                caption = visual.find('span', class_='ph_d').text.strip()
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption if (caption) else ''
                })
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
        page['body'] = "\n".join([p.text.strip() for p in p_tags if len(p.text) > 0])
        time_string = soup.find('meta', property='article:published_time')
        page['publish_time'] = strftime('%Y-%m-%d %H:%M:%S', strptime(time_string['content'][:-7], '%Y-%m-%dT%H:%M:%S'))
        
        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if soup.find('div', class_='keyword boxTitle'):
            keywords = soup.find('div', class_='keyword boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())

        # -- 取出記者 ---
        author = article_title.find('span').text.strip()
        page['authors'] = re.findall(r'文／記者(\w*)', author)
        
        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        visuals = article_content.find_all('span', class_=['ph_b', 'ph_d1'])
        for visual in visuals:
            img = visual.find('img')
            if visual.find('span', class_='ph_d'):
                caption = visual.find('span', class_='ph_d').text.strip()
            else:
                caption = ""
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img['src'],
                    'caption': caption
                })
        return page

    def __health_category(self, soup):
        """
        取出 health 類別需要的資料內容
        """
        page = dict()
        article = soup.find('div', class_='whitecon articlebody')
        page['title'] = article.h1.text.strip()
        article_content = soup.find('div', itemprop='articleBody')
        p_tags = article_content.find_all('p',recursive=False)
        page['body'] = "\n".join([p.text for p in p_tags if len(p.text) > 0])
        page['publish_time'] = article_content.find_all('span')[0].text + ':00'

        # --- 取出關鍵字 ---
        page['keywords'] = list()
        if article.find('div', class_='keyword boxTitle'):
            keywords = article.find('div', class_='keyword boxTitle').find_all('a')
            for keyword in keywords:
                page['keywords'].append(keyword.text.strip())
        elif soup.find('meta', attr={'name':'keywords'}):
            # 2018-11-18 自由時報全類別改版移除關鍵字區塊，改由 Meta 取得
            meta_keywords = soup.find('meta', attr={'name':'keywords'})
            keywords = meta_keywords['content'].split(',')
            for keyword in keywords:
                page['keywords'].append(keyword.strip())
        
        # -- 取出記者 ---
        page['authors'] = self.extract_author(page['body'])
        return page

    def __partners_category(self, soup):
        """
        取出 partners 類別需要的資料內容
        """
        page = dict()
        #news
        page['title'] = soup.h1.text.strip()
        page['publish_time'] = re.sub(r'\|[ ]+', '', soup.find('small').find_all('span')[1].text)
        page['keywords'] = [x.text for x in soup.find('div', class_='keyword').find_all('a')]
        page['authors'] = re.compile(r"記者(\w*)").findall(soup.find('small').text)

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()

        imgs = soup.find_all('div', class_='pic')
        for img in imgs:
            page['visual_contents'].append(
                {
                    'type': 1,
                    'visual_src': img.img['src'],
                    'caption': img.text
                })

        # --- 取出內文 ---
        while soup.find('span') != None:
            soup.find('span').decompose()

        article_content = [x.text for x in soup.find('div', class_='text').find_all('p', recursive = False) if x.text!='' and x.text.find('\u3000\n')<0 and x.text.find('往下閱讀')<0]
        page['body'] = re.sub(r'[\n]+','\n', "\n".join(article_content))
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
        elif category == 'health':
            news_page = self.__health_category(soup)
        elif category == 'partners':
            news_page = self.__partners_category(soup)
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

    def fetch_publish_time(self):
        """
        發佈時間併入各個類別中爬梳
        """
        pass
    
    def extract_author(self, content):
        author = self.regex_pattern.findall(content)
        return author

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
                if status_code == requests.codes.ok:
                    page_type = self.extract_type(html_content['redirected_url'])
                    print('crawling...[{}] id: {}'.format(page_type, row['id']))

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw['list_id'] = row['id']
                        news_page_raw['url'] = row['url']
                        news_page_raw['url_md5'] = row['url_md5']
                        news_page_raw['page_content'] =  self.compress_html(html_content['html'])
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print('Save ' + str(row['id']) + ' page Raw.')
                    
                    soup = BeautifulSoup(html_content['html'], 'html.parser')
                    news_page = self.fetch_news_content(page_type, soup)
                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id
                    news_page['image'] = len(news_page['visual_contents'])
                    news_page['video'] = 0
                    news_page['publish_time'] = re.sub('[ ]+', ' ', news_page['publish_time'])
                    news_page['publish_time'] = news_page['publish_time'][:19]

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
                self.logme.exception('error: list-' + str(row['id']) + str(e.args))
                # 更新錯誤次數記錄
                self.floodfire_storage.update_list_errorcount(row['url_md5'])
                pass
        self.logme.info('Crawled ' + str(crawl_count) + ' ' + self.code_name + '-news lists.')
        
        # 單頁測試
        # status_code, html_content = self.fetch_html('http://auto.ltn.com.tw/news/11187/2')
        # if status_code == requests.codes.ok:
        #     page_type = self.extract_type(html_content['redirected_url'])
        #     soup = BeautifulSoup(html_content['html'], 'html.parser')
        #     news_page = self.fetch_news_content(page_type, soup)
        #     print(news_page)
        #     # 儲存圖片或影像資訊
        #     if page_visual and len(news_page['visual_contents']) > 0:
        #         for vistual_row in news_page['visual_contents']:
        #             vistual_row['list_id'] = 100
        #             vistual_row['url_md5'] = '60420fb89e8141139755f7f99ddf8e4e'
        #             self.floodfire_storage.insert_visual_link(vistual_row)

            # minhtml = self.compress_html(html_content['html'])
            # print(minhtml)
