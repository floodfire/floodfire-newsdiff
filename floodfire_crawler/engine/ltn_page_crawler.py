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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            }
            response = requests.get(url, headers=headers, timeout=15)
            resp_content = {
                "redirected_url": response.url,  # 取得最後 redirect 之後的真實網址
                "html": response.text,
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
        取出網頁中的新聞內容

        Keyword arguments:
            soup (beautifulsoup) -- 已經 parse 過的 BeautifulSoup 物件
        """
        # 看到下列話句，後面的都不看
        break_contents = [
            "見前文：",
            "成為粉絲，看更多汽車情報->《自由時報汽車頻道粉絲團》",
            "\n    一手掌握經濟脈動\n    點我訂閱自由財經Youtube頻道\n",
        ]
        news_page = dict()
        # --- 取出標題 ---
        news_page["title"] = soup.find_all("h1")[-1].text.strip()
        # --- 取出內文 ---
        soup_content = soup.find_all("div", class_="text")[-1]
        p_tags = soup_content.find_all("p", recursive=False)
        p_content = [
            p.text
            for p in p_tags
            if not p.has_attr("class")
            and not p.has_attr("style")
            and p.img is None
            and p.br is None
        ]
        actual_contents = []
        for content in p_content:
            if content in break_contents:
                break
            else:
                actual_contents.append(content)
        news_page["body"] = "\n".join(actual_contents)

        # --- 取出關鍵字 ---
        news_page["keywords"] = list()
        keyword_scrips = [
            x.text for x in soup.findAll("script") if x.text.find('"keywords":') > 0
        ]
        if len(keyword_scrips) > 0:
            kw_str = keyword_scrips[0]
            kw_list = kw_str.split('keywords": "')[1].split('"')[0].split(",")
            news_page["keywords"] = [x for x in kw_list if x != ""]
        else:
            news_page["keywords"] = []

        # -- 取出發布時間 ---
        time_section = soup.find_all(class_="time")[-1]
        news_page["publish_time"] = (
            " ".join(
                time_section.find(text=True, recursive=False).strip().split(" ")[:2]
            )
            + ":00"
        )
        # -- 取出記者 ---
        if soup.find(class_="author") is not None:
            author = soup.find(class_="author").text.strip()
            # 為了避免區塊性的作者
            author = [x for x in author.split("\n") if x != ""][0]
            news_page["authors"] = re.findall(r"文／記者(\w*)", author)
            if len(news_page["authors"]) == 0:
                # e.g. 3C科技頻道／綜合報導，擷取前半部
                news_page["authors"] = [author.split("／")[0]]
        elif soup.find(class_="auther") is not None:
            author = soup.find(class_="auther").text.strip()
            # 為了避免區塊性的作者
            author = [x for x in author.split("\n") if x != ""][0]
            news_page["authors"] = re.findall(r"文／記者(\w*)", author)
            if len(news_page["authors"]) == 0:
                # e.g. 3C科技頻道／綜合報導，擷取前半部
                news_page["authors"] = [author.split("／")[0]]
        else:
            news_page["authors"] = []

        # -- 取出視覺資料連結（圖片） ---
        news_page["visual_contents"] = list()

        visuals = soup.find_all("span", class_="ph_b")
        for visual in visuals:
            img = visual.find("img")
            # 找圖片網址
            if img.has_attr("data-original"):
                img_url = img["data-original"]
            elif img.has_attr("src"):
                img_url = img["src"]
            else:
                continue
            # 找圖片文字
            if visual.find("span", class_="ph_d") is not None:
                caption = visual.find("span", class_="ph_d").text.strip()
            else:
                caption = ""
            news_page["visual_contents"].append(
                {"type": 1, "visual_src": img_url, "caption": caption}
            )
        return news_page

    def fetch_publish_time(self):
        """
        發佈時間併入各個類別中爬梳
        """
        pass

    def extract_author(self, content):
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
        crawl_list = self.floodfire_storage.get_crawllist(
            source_id, page_diff, diff_obj
        )
        # log 起始訊息
        start_msg = (
            "Start crawling "
            + str(len(crawl_list))
            + " "
            + self.code_name
            + "-news lists."
        )
        if page_raw:
            start_msg += " --with save RAW"
        if page_visual:
            start_msg += " --with save VISUAL_LINK"
        self.logme.info(start_msg)
        # 本次的爬抓計數
        crawl_count = 0

        for row in crawl_list:
            try:
                status_code, html_content = self.fetch_html(row["url"])
                if status_code == requests.codes.ok:
                    print("crawling...id: {}".format(row["id"]))

                    if page_raw:
                        news_page_raw = dict()
                        news_page_raw["list_id"] = row["id"]
                        news_page_raw["url"] = row["url"]
                        news_page_raw["url_md5"] = row["url_md5"]
                        news_page_raw["page_content"] = self.compress_html(
                            html_content["html"]
                        )
                        self.floodfire_storage.insert_page_raw(news_page_raw)
                        print("Save " + str(row["id"]) + " page Raw.")

                    soup = BeautifulSoup(html_content["html"], "html.parser")
                    news_page = self.fetch_news_content(soup)
                    news_page["list_id"] = row["id"]
                    news_page["url"] = row["url"]
                    news_page["url_md5"] = row["url_md5"]
                    news_page["redirected_url"] = html_content["redirected_url"]
                    news_page["source_id"] = source_id
                    news_page["image"] = len(news_page["visual_contents"])
                    news_page["video"] = 0
                    news_page["publish_time"] = re.sub(
                        "[ ]+", " ", news_page["publish_time"]
                    )
                    news_page["publish_time"] = news_page["publish_time"].replace(
                        "/", "-"
                    )
                    news_page["publish_time"] = news_page["publish_time"][:19]

                    ######Diff#######
                    version = 1
                    table_name = None
                    diff_vals = (version, None, None)
                    if page_diff:
                        last_page, table_name = self.floodfire_storage.get_last_page(
                            news_page["url_md5"],
                            news_page["publish_time"],
                            diff_obj.compared_cols,
                        )
                        if last_page != None:
                            diff_col_list = diff_obj.page_diff(news_page, last_page)
                            if diff_col_list is None:
                                # 有上一筆，但沒有不同，更新爬抓次數，不儲存
                                print("has last, no diff")
                                crawl_count += 1
                                self.floodfire_storage.update_list_crawlercount(
                                    row["url_md5"]
                                )
                                continue
                            else:
                                # 出現Diff，儲存
                                version = last_page["version"] + 1
                                last_page_id = last_page["id"]
                                diff_cols = ",".join(diff_col_list)
                                diff_vals = (version, last_page_id, diff_cols)
                    ######Diff#######
                    print(diff_vals)
                    if self.floodfire_storage.insert_page(
                        news_page, table_name, diff_vals
                    ):
                        # 更新爬抓次數記錄
                        self.floodfire_storage.update_list_crawlercount(row["url_md5"])
                        self.floodfire_storage.update_list_versioncount(row["url_md5"])
                        # 本次爬抓計數+1
                        crawl_count += 1
                    else:
                        # 更新錯誤次數記錄
                        self.floodfire_storage.update_list_errorcount(row["url_md5"])

                    # 儲存圖片或影像資訊
                    if page_visual and len(news_page["visual_contents"]) > 0:
                        for vistual_row in news_page["visual_contents"]:
                            vistual_row["list_id"] = row["id"]
                            vistual_row["url_md5"] = row["url_md5"]
                            self.floodfire_storage.insert_visual_link(
                                vistual_row, version
                            )

                    # 隨機睡 2~6 秒再進入下一筆抓取
                    sleep(randint(2, 6))
                else:
                    # get 網頁失敗的時候更新 error count
                    self.floodfire_storage.update_list_errorcount(row["url_md5"])
            except Exception as e:
                self.logme.exception("error: list-" + str(row["id"]) + str(e.args))
                # 更新錯誤次數記錄
                self.floodfire_storage.update_list_errorcount(row["url_md5"])
                pass
        self.logme.info(
            "Crawled " + str(crawl_count) + " " + self.code_name + "-news lists."
        )
