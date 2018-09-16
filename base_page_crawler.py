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
    def fetch_news_content(self, page):
        """
        傳回新聞頁面中的內容
        """
        return NotImplemented