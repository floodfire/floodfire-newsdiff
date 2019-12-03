#!/usr/bin/env python3

import os
import logging
from logging import handlers
from argparse import ArgumentParser
from configparser import ConfigParser
from floodfire_crawler.engine.ltn_list_crawler import LtnListCrawler
from floodfire_crawler.engine.apd_list_crawler import ApdListCrawler
from floodfire_crawler.engine.udn_list_crawler import UdnListCrawler
from floodfire_crawler.engine.ett_list_crawler import EttListCrawler
from floodfire_crawler.engine.ltn_page_crawler import LtnPageCrawler
from floodfire_crawler.engine.apd_page_crawler import ApdPageCrawler
from floodfire_crawler.engine.ett_page_crawler import EttPageCrawler
from floodfire_crawler.engine.udn_page_crawler import UdnPageCrawler
from floodfire_crawler.engine.cnt_list_crawler import CntListCrawler
from floodfire_crawler.engine.cnt_page_crawler import CntPageCrawler
from floodfire_crawler.engine.cna_list_crawler import CnaListCrawler
from floodfire_crawler.engine.cna_page_crawler import CnaPageCrawler
from floodfire_crawler.engine.ntk_list_crawler import NtkListCrawler
from floodfire_crawler.engine.ntk_page_crawler import NtkPageCrawler

class Crawler():
    def __init__(self, args):
        self.args = args
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.config = ConfigParser()
        self.config.read(dir_path + '/config.ini')

        file_handler_err = handlers.RotatingFileHandler(dir_path + '/log/crawler.log',maxBytes=1048576,backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
        file_handler_err.setFormatter(file_formatter)
        self.logme = logging.getLogger(self.args.media)
        self.logme.setLevel(logging.INFO)
        self.logme.addHandler(file_handler_err)
        
    def __ltn(self):
        """
        自由時報執行區間
        """
        if self.args.typeof == 'list':
            llc = LtnListCrawler(self.config)
            llc.url = 'https://news.ltn.com.tw/ajax/breakingnews/all/'
            llc.run()

        elif self.args.typeof == 'page':
            lpc = LtnPageCrawler(self.config, self.logme)
            lpc.run(self.args.raw, self.args.diff, self.args.visual)
    
    def __apd(self):
        """
        蘋果日報執行區間
        """
        if self.args.typeof == 'list':
            alc = ApdListCrawler(self.config)
            alc.url = 'https://tw.appledaily.com/new'
            alc.run()
        elif self.args.typeof == 'page':
            apc = ApdPageCrawler(self.config, self.logme)
            apc.run(self.args.raw, self.args.diff, self.args.visual)

    def __cnt(self):
        """
        中國時報執行區間
        """
        if self.args.typeof == 'list':
            clc = CntListCrawler(self.config)
            clc.url = 'https://www.chinatimes.com/realtimenews'
            clc.run()
        elif self.args.typeof == 'page':
            cpc = CntPageCrawler(self.config, self.logme)
            cpc.run(self.args.raw, self.args.diff, self.args.visual)
          
    def __udn(self):
        """
        聯合新聞網執行區間
        """
        if self.args.typeof == 'list':
            ulc = UdnListCrawler(self.config)
            ulc.url = 'https://udn.com/news/breaknews/1'
            ulc.run()
        elif self.args.typeof == 'page':
            upc = UdnPageCrawler(self.config, self.logme)
            upc.run(self.args.raw, self.args.diff, self.args.visual)
    
    def __ett(self):
        """
        ETToday執行區間
        """
        if self.args.typeof == 'list':
            elc = EttListCrawler(self.config)
            elc.url = 'https://www.ettoday.net/news/news-list.htm'
            elc.run()
        elif self.args.typeof == 'page':
            epc = EttPageCrawler(self.config, self.logme)
            epc.run(self.args.raw, self.args.diff, self.args.visual)

    def __cna(self):
        """
        中央社執行區間
        """
        if self.args.typeof == 'list':
            clc = CnaListCrawler(self.config)
            clc.url = 'https://www.cna.com.tw/list/aall.aspx'
            clc.run()
        elif self.args.typeof == 'page':
            cpc = CnaPageCrawler(self.config, self.logme)
            cpc.run(self.args.raw, self.args.diff, self.args.visual)
    
    def __ntk(self):
        """
        newtalk 執行區間
        """
        if self.args.typeof == 'list':
            ntk = NtkListCrawler(self.config)
            ntk.url = ''
            ntk.run()
        elif self.args.typeof == 'page':
            ntk = NtkPageCrawler(self.config, self.logme)
            ntk.run(self.args.raw, self.args.diff, self.args.visual)
    
    def main(self):
 
        if self.args.media == 'ltn':
            self.__ltn()
            
        if self.args.media == 'apd':
            self.__apd()

        if self.args.media == 'cnt':
            self.__cnt()
            
        if self.args.media == 'udn':
            self.__udn()
        
        if self.args.media == 'ett':
            self.__ett()

        if self.args.media == 'cna':
            self.__cna()

if __name__ == '__main__':
    parser = ArgumentParser(description="水火新聞爬蟲")
    parser.add_argument("media", help="指定爬抓的媒體")
    parser.add_argument("typeof", choices=['list', 'page'], 
                        default='list', help="爬抓的類別：列表、頁面")
    parser.add_argument("-w", "--raw", action="store_true",
                        help="儲存網頁原始內容")
    parser.add_argument("-d", "--diff", action="store_true",
                        help="儲存網頁 Diff 差異")
    parser.add_argument("-v", "--visual", action="store_true",
                        help="儲存網頁 media 連結內容")
    args = parser.parse_args()
    
    c = Crawler(args)
    c.main()
