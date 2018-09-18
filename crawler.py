#!/usr/bin/env python3

import os
from argparse import ArgumentParser
from floodfire_crawler.engine.ltn_list_crawler import LtnListCrawler
from configparser import ConfigParser

class Crawler():
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.config = ConfigParser()
        self.config.read(dir_path + '/config.ini')
        
    def __ltn(self, args):
        llc = LtnListCrawler()
        llc.url = 'http://news.ltn.com.tw/list/breakingnews'
        llc.run()

    def main(self):
        parser = ArgumentParser(description="水火新聞爬蟲")
        parser.add_argument("media", help="指定爬抓的媒體")
        parser.add_argument("typeof", choices=['list', 'page'], 
                            default='list', help="爬抓的類別：列表、頁面")
        parser.add_argument("-w", "--raw", action="store_true",
                            help="儲存網頁原始內容")
        parser.add_argument("-d", "--diff", action="store_true",
                            help="儲存網頁 Diff 差異")
        args = parser.parse_args()

        if args.media == 'ltn':
            self.__ltn(args)

if __name__ == '__main__':
    c = Crawler()
    c.main()
