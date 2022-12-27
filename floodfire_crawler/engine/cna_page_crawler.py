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
import demoji


class CnaPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "cna"
        self.floodfire_storage = FloodfireStorage(config)
        self.logme = logme
        demoji.download_codes()

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
        fake_img_list = [
            'https://img5.cna.com.tw/www/WebPhotos/1024/20190429/800x600_008142228170.jpg']
        page = {}
        all_article = soup.find('div', class_='centralContent')
        # --- 取出標題 ---
        page['title'] = all_article.h1.text.strip()

        # --- 取出內文 ---
        content = '\n'.join([
            x.text for x in
            all_article.find('div', class_='paragraph').find_all('p')
        ])
        page['body'] = demoji.replace(content, '')

        # --- 取出發布時間 ---
        page['publish_time'] = self.fetch_publish_time(all_article)

        # --- 取出關鍵字 ---
        # keywords
        page['keywords'] = [
            x.text for x in
            all_article.find_all('div', class_='keywordTag')
        ]
        # --- 取出記者 ---
        # authors
        get_author = list()
        get_in_parenthesis = re.findall('(?:（|\()(.*?)(?:）|\))', content)
        first_line_author = get_in_parenthesis[0].split('記者')
        place_list = ['台北', '新北', '桃園', '台中', '台南', '高雄', '基隆', '新竹', '嘉義',
                      '苗栗', '彰化', '南投', '雲林', '屏東', '宜蘭', '花蓮', '台東', '澎湖', '金門', '馬祖']
        if len(first_line_author) > 1:
            author_in_parenthesis = first_line_author[1].split('、')
            for i in range(len(author_in_parenthesis)):
                if i == len(author_in_parenthesis)-1:
                    for place in place_list:
                        if place in author_in_parenthesis[i]:
                            get_author_last = author_in_parenthesis[i].split(
                                place)
                            if get_author_last[0] not in get_author:
                                get_author.append(get_author_last[0])
                            break
                        else:
                            if author_in_parenthesis[i][:3] not in get_author:
                                get_author.append(author_in_parenthesis[i][:3])
                else:
                    if author_in_parenthesis[i] not in get_author:
                        get_author.append(author_in_parenthesis[i])

        for i in range(len(get_in_parenthesis)):
            if '譯者：' in get_in_parenthesis[i]:
                author_list = get_in_parenthesis[i].split('/')
                get_author.append(author_list[0][3:]+'(譯)')
            if '編輯：' in get_in_parenthesis[i]:
                if '\\' in get_in_parenthesis[i]:
                    author_list = get_in_parenthesis[i].split('\\')
                else:
                    author_list = get_in_parenthesis[i].split('/')
                get_author.append(author_list[0][3:])
                if len(author_list) > 1:
                    for i in range(1, len(author_list)):
                        if author_list[i] not in get_author:
                            get_author.append(author_list[i])

        page['authors'] = get_author

        # --- 取出圖片數 ---
        # has_image
        image_list = soup.find_all('div', {'class': 'floatImg center'})
        for i in image_list:
            for j in fake_img_list:
                if str(j) in str(i):
                    image_list.remove(i)

        page['image'] = len(image_list)

        # -- 取出視覺資料連結（圖片） ---
        page['visual_contents'] = list()
        for i in range(len(image_list)):
            img_content = image_list[i].find('img')
            if image_list[i].find('div', class_='picinfo') is not None:
                caption = image_list[i].find('div', class_='picinfo').text
            else:
                caption = ''
            page['visual_contents'].append({
                'type': 1,
                'visual_src': img_content['data-src'] if 'data-src' in str(img_content) else img_content['src'],
                'caption': caption
            })

        # --- 取出影片數 ---
        # has_video
        video_list = soup.find_all('div', {'class': 'youtubeBox'})
        page['video'] = len(video_list)
        for i in range(len(video_list)):
            page['visual_contents'].append({
                'type': 2,
                'visual_src': video_list[i].find('iframe')['data-src'],
                'caption': video_list[i].find_all('div', {'class': 'picinfo'})[0].text if len(video_list[i].find_all('div', {'class': 'picinfo'})) > 0 else ''
            })

        outerMedia_list = soup.find_all(
            lambda tag: tag.name == 'div' and tag.get('class') == ['outerMedia'])

        for i in range(len(outerMedia_list)):
            if 'data-href' in str(outerMedia_list[i]):
                if 'fb-post' in str(outerMedia_list[i]):
                    page['image'] += 1
                    url_tag = outerMedia_list[i].find(
                        'div', {'class': 'fb-post'})
                    page['visual_contents'].append({
                        'type': 1,
                        'visual_src': url_tag['data-href'],
                        'caption': ''
                    })
                elif 'fb-video' in str(outerMedia_list[i]):
                    url_tag = outerMedia_list[i].find(
                        'div', {'class': 'fb-video'})
                    page['video'] += 1
                    page['visual_contents'].append({
                        'type': 2,
                        'visual_src': url_tag['data-href'],
                        'caption': ''
                    })
            elif 'href' in str(outerMedia_list[i]):
                url_tag = outerMedia_list[i].find('a', href=True)
                url = url_tag['href']
                page['video'] += 1
                page['visual_contents'].append({
                    'type': 2,
                    'visual_src': url_tag['href'],
                    'caption': ''
                })

        # -- 取出視覺資料連結（影片） ---

        """
        #可以擷取影片網址以及影片截圖
        video_box = soup.find('div',{'id':'videobox'})

        re.findall('https?://(?:[-\w./])+.(?:mp4)', video_box.select('script')[-1].text)[0]
        
        re.findall('https?://(?:[-\w./])+.(?:jpg|gif|png)', video_box.select('script')[-1].text)[0]

        """
        return page

    def fetch_publish_time(self, soup):
        time = soup.find('div', class_='updatetime').text.strip()
        time = time.split('（')[0]
        news_time = strftime(
            '%Y-%m-%d %H:%M:%S', strptime(time[time.find('：')+1:], '%Y/%m/%d %H:%M'))
        return(news_time)

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
        # crawl_category = ['news', 'ent', 'ec', 'sports']
        source_id = self.floodfire_storage.get_source_id(self.code_name)
        ######Diff#######
        if page_diff:
            diff_obj = FloodfireDiff()
        else:
            diff_obj = None
        ######Diff#######
        crawl_list = self.floodfire_storage.get_crawllist(
            source_id, page_diff, diff_obj)
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
                    if(soup.contents[0] != 'html'):
                        self.floodfire_storage.update_list_errorcount(
                            row['url_md5'])
                        continue
                    news_page = self.fetch_news_content(soup)
                    news_page['list_id'] = row['id']
                    news_page['url'] = row['url']
                    news_page['url_md5'] = row['url_md5']
                    news_page['redirected_url'] = html_content['redirected_url']
                    news_page['source_id'] = source_id

                    ######Diff#######
                    version = 1
                    table_name = None
                    diff_vals = (version, None, None)
                    if page_diff:
                        last_page, table_name = self.floodfire_storage.get_last_page(news_page['url_md5'],
                                                                                     news_page['publish_time'],
                                                                                     diff_obj.compared_cols)
                        if last_page != None:
                            diff_col_list = diff_obj.page_diff(
                                news_page, last_page)
                            if diff_col_list is None:
                                # 有上一筆，但沒有不同，更新爬抓次數，不儲存
                                print('has last, no diff')
                                crawl_count += 1
                                self.floodfire_storage.update_list_crawlercount(
                                    row['url_md5'])
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
                        self.floodfire_storage.update_list_crawlercount(
                            row['url_md5'])
                        self.floodfire_storage.update_list_versioncount(
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
                            self.floodfire_storage.insert_visual_link(
                                vistual_row, version)

                    # 隨機睡 2~6 秒再進入下一筆抓取
                    sleep(randint(2, 6))
                else:
                    # get 網頁失敗的時候更新 error count
                    self.floodfire_storage.update_list_errorcount(
                        row['url_md5'])
            except Exception as e:
                self.logme.exception(
                    'error: list-' + str(row['id']) + ' ' + str(e.args))
                # 更新錯誤次數記錄
                self.floodfire_storage.update_list_errorcount(row['url_md5'])
                pass
        self.logme.info('Crawled ' + str(crawl_count) +
                        ' ' + self.code_name + '-news lists.')
