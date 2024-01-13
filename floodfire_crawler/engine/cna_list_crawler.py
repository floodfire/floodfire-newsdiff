#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from hashlib import md5
from time import sleep
from floodfire_crawler.core.base_list_crawler import BaseListCrawler
from floodfire_crawler.storage.rdb_storage import FloodfireStorage


class CnaListCrawler(BaseListCrawler):
    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    def __init__(self, config):
        self.floodfire_storage = FloodfireStorage(config)

    def fetch_html(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        return html

    def fetch_list(self, soup):
        news_cat_dic = {
            "aipl": "政治",
            "aopl": "國際",
            "acn": "兩岸",
            "aie": "產經",
            "afe": "產經-證券",
            "asc": "證券",
            "ait": "科技",
            "ahel": "生活",
            "asoc": "社會",
            "aloc": "地方",
            "acul": "文化",
            "aspt": "運動",
            "amov": "娛樂",
        }
        news = []
        total_news_rows = soup.find_all("ul", {"id": "jsMainList"})
        news_rows = total_news_rows[0].find_all("li")
        # md5hash = md5()
        for news_row in news_rows:
            category = ""
            link_a = news_row.find("a")
            if "javascript:" in link_a["href"]:
                continue
            url = link_a["href"]
            if url[:4] != "http":
                url = "https://www.cna.com.tw" + url
            md5hash = md5(url.encode("utf-8")).hexdigest()
            category_eng = link_a["href"].split("/")[2]
            if category_eng in news_cat_dic:
                category = news_cat_dic[category_eng]
            else:
                category = category_eng
            raw = {
                "title": link_a.h2.text.strip().replace("　", " ").replace("\u200b", ""),
                "url": url,
                "url_md5": md5hash,
                "source_id": 3,
                "category": category,
            }
            news.append(raw)
        return news

    def fetch_list2(self, response_json):
        news = []
        for i in response_json["ResultData"]["Items"]:
            row = {
                "title": i["HeadLine"],
                "url": i["PageUrl"],
                "url_md5": md5(i["PageUrl"].encode("utf-8")).hexdigest(),
                "source_id": 3,
                "category": i["ClassName"],
            }
            news.append(row)
        return news

    def make_a_round(self):
        consecutive = 0
        html = self.fetch_html(self.url)
        soup = BeautifulSoup(html, "html.parser")
        news_list = self.fetch_list(soup)
        print(len(news_list))
        for news in news_list:
            if consecutive > 20:
                print("News consecutive more then 20, stop crawler!!")
                break
            if self.floodfire_storage.check_list(news["url_md5"]) == 0:
                self.floodfire_storage.insert_list(news)
            else:
                print(news["title"] + " exist! skip insert.")
                consecutive += 1
        print("1 page done !")
        offset = 1
        page_url = "https://www.cna.com.tw/cna2018api/api/WNewsList"
        while consecutive <= 20:
            news_list = []
            offset += 1
            sleep(2)
            post_data = {
                "action": "0",
                "category": "aall",
                "pageidx": offset,
                "pagesize": 20,
            }
            response = requests.post(page_url, data=post_data).json()
            news_list = self.fetch_list2(response)
            print(len(news_list))
            if len(response["ResultData"]["Items"]) == 0:
                print("no page!")
                break
            for news in news_list:
                if self.floodfire_storage.check_list(news["url_md5"]) == 0:
                    self.floodfire_storage.insert_list(news)
                else:
                    print(news["title"] + " exist! skip insert.")
                    consecutive += 1
                    print(consecutive)
            print(str(offset) + " page done !")

    def run(self):
        self.make_a_round()
        """
        news_list = self.fetch_list(soup)
        print(news_list)
        for news in news_list:
            if(self.floodfire_storage.check_list(news['url_md5']) == 0):
                self.floodfire_storage.insert_list(news)
            else:
                print(news['title']+' exist! skip insert.')
            
        last_page = self.get_last(soup)
        print(last_page)
        """
