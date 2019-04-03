#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class BasePageCrawler(metaclass=ABCMeta):

    @abstractmethod
    def fetch_html(self, url):
        """
        傳回新聞頁面的 HTML
        """
        return NotImplemented

    @abstractmethod
    def fetch_news_content(self, soup):
        """
        傳回新聞頁面中的內容

        keyward arguments:
            soup (object) -- beautifulsoup object
        """
        return NotImplemented

    @abstractmethod
    def fetch_publish_time(self, soup):
        """
        取得新聞發佈時間

        keyward arguments:
            soup (object) -- beautifulsoup object
        """
        return NotImplemented
    
    @abstractmethod
    def run(self):
        """
        程式執行點
        """
        return NotImplemented