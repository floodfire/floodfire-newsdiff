#!/usr/bin/env python3

from abc import ABCMeta, abstractmethod

class BaseListCrawler(metaclass=ABCMeta):
    _url = ''

    @property
    @abstractmethod
    def url(self):
        return self._url

    @url.setter
    @abstractmethod
    def url(self, value):
        self._url = value

    @abstractmethod
    def fetch_html(self, url):
        """
        傳回 List 頁面的 HTML
        """
        return NotImplemented
    
    @abstractmethod
    def fetch_list(self, soup):
        """
        傳回 HTML 中所有的 List
        """
        return NotImplemented

    @abstractmethod
    def run(self):
        """
        程式執行點
        """
        return NotImplemented