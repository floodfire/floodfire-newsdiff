#!/usr/bin/env python3

import os
import logging
from logging import handlers
from argparse import ArgumentParser
from configparser import ConfigParser
from floodfire_crawler.engine.ltn_list_crawler import LtnListCrawler
from floodfire_crawler.engine.apd_list_crawler import ApdListCrawler
from floodfire_crawler.engine.ltn_page_crawler import LtnPageCrawler
from floodfire_crawler.engine.apd_page_crawler import ApdPageCrawler

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
        if self.args.typeof == 'list':
            llc = LtnListCrawler(self.config)
            llc.url = 'http://news.ltn.com.tw/list/breakingnews'
            llc.run()
        elif self.args.typeof == 'page':
            lpc = LtnPageCrawler(self.config, self.logme)
            lpc.run()
    
    def __apd(self):
        if self.args.typeof == 'list':
            plc = ApdListCrawler(self.config)
            plc.url = 'https://tw.appledaily.com/new'
            plc.run()
        elif self.args.typeof == 'page':
            plc = ApdPageCrawler(self.config, self.logme)
            plc.run()
        
    def main(self):
 
        if self.args.media == 'ltn':
            self.__ltn()
            
        if self.args.media == 'apd':
            self.__apd()

if __name__ == '__main__':
    parser = ArgumentParser(description="水火新聞爬蟲")
    parser.add_argument("media", help="指定爬抓的媒體")
    parser.add_argument("typeof", choices=['list', 'page'], 
                        default='list', help="爬抓的類別：列表、頁面")
    parser.add_argument("-w", "--raw", action="store_true",
                        help="儲存網頁原始內容")
    parser.add_argument("-d", "--diff", action="store_true",
                        help="儲存網頁 Diff 差異")
    args = parser.parse_args()
    
    c = Crawler(args)
    c.main()
