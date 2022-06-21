#!/usr/bin/env python3

import requests
import re
import htmlmin
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from time import sleep, strftime, strptime
from random import randint
from floodfire_crawler.core.base_page_crawler import BasePageCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage
from floodfire_crawler.service.diff import FloodfireDiff
import demoji


class ApdPageCrawler(BasePageCrawler):

    def __init__(self, config, logme):
        self.code_name = "apd"
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
        # 初始數值 & 取出script中的json
        report = {}
        script_json = self.get_script_json(soup)

        # --- 取出標題 ---
        title = soup.h1.text.replace('\u3000', '　')
        report['title'] = demoji.replace(title, '')

        # --- 取出內文 ---
        content = '\n'.join([x.get_text("\n") for x in soup.find_all('p')])
        report['body'] = demoji.replace(content, '')

        # --- 取出記者 ---
        # (XXX/XX報導) (曾珮瑛、張世瑜/高雄報導) https://regex101.com/r/DvppFX/1
        author = re.search(
            r'[(（](.*?中心)?(.*?)(／|\/|╱)(.*?)報導[）)]', report['body'])
        if author is not None:
            author_str = author.group(2)
        else:
            author_str = ''
        left_bracket_pos = max(author_str.rfind('('), author_str.rfind('（'))
        if (left_bracket_pos > 0):
            author_str = author_str[(left_bracket_pos+1):]
        report['authors'] = author_str.split('、')

        # --- 取出發布時間 ---
        report['publish_time'] = self.fetch_publish_time(
            script_json['datePublished']
        )

        # --- 取出關鍵字 ---
        tags = []
        tag_container = soup.find('div', {"class": "tags-container"})
        if tag_container is not None:
            for a_tag in tag_container.find_all('a'):
                tags.append(a_tag.text)
        report['keywords'] = tags

        # --- 取出圖片 ---
        images = []
        # 取出封面照片
        cover_images = soup.find_all('figure', {'class': 'flex'})
        for cover_image in cover_images:
            image = {
                'type': 1,
                'visual_src': cover_image.img['src'],
                'caption': cover_image.img['alt'],
            }
            images.append(image)
        other_images = soup.find_all('figure', {'class': 'visual__image'})
        for other_image in other_images:
            image = {
                'type': 1,
                'visual_src': other_image.img['src'],
                'caption': other_image.parent.parent.find('div', {'class': 'image_text'}).text,
            }
            images.append(image)
        report['image'] = len(images)
        report['visual_contents'] = images

        # -- 取出影片 ---
        videos = self.get_video_info(soup)
        report['video'] = len(videos)
        for video in videos:
            report['visual_contents'].append(video)

        return report

    def get_video_info(self, soup):
        videos = []
        scripts = soup.find_all('script')
        for script in scripts:
            if script.text.find('videoConfig') > 0:
                video = {
                    'type': 2,
                    'visual_src': script.text.split("src: '")[1].split("'")[0],
                    'caption': ''
                }
                videos.append(video)
        return videos

    def get_script_json(self, soup):
        """
        從soup物件中取出javascript中的json檔
        Keyword arguments:
            soup (object) -- soup物件
        Output
            json (dict) -- script中的json物件
        """
        myjson_str = [x for x in soup.find_all('script') if x.has_attr(
            'type') and x['type'] == 'application/ld+json'][0]
        myjson_str_list = myjson_str.text.replace(
            '\r', '').replace('\t', '').split('\n')
        content_list = []
        # 去除註解
        for mystring in myjson_str_list:
            is_outside = True
            is_add = True
            for i in range(len(mystring)):
                chat_txt = mystring[i]
                if chat_txt == '"':
                    is_outside = not is_outside
                if chat_txt == '/' and is_outside:
                    content_list.append(mystring[:i].replace('\t', '  '))
                    is_add = False
                    break
            if is_add:
                content_list.append(mystring.replace('\t', '  '))

        myjson = json.loads(''.join(content_list), strict=False)
        if type(myjson) == list:
            myjson = myjson[0]
        return myjson

    def fetch_publish_time(self, timeString):
        # timeString e.g 2022-06-20T12:18:00+08:00
        news_time = strftime(
            '%Y-%m-%d %H:%M:%S',
            strptime(timeString, '%Y-%m-%dT%H:%M:%S+08:00')
        )
        return(news_time)

    def compress_html(self, page_json):
        """
        Deprecated in this news source
        """
        return page_json

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
            source_id, page_diff, diff_obj
        )
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
                        news_page_raw['page_content'] = json.dumps(
                            html_content['json'])
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
