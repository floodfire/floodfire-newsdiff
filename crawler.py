#!/usr/bin/env python3

from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="水火新聞爬蟲")
    parser.add_argument("media", help="指定爬抓的媒體")
    parser.add_argument("typeof", choices=['list', 'page'], 
                        default='list', help="爬抓的類別：列表、頁面")
    parser.add_argument("-w", "--raw", action="store_true",
                        help="儲存網頁原始內容")
    parser.add_argument("-d", "--diff", action="store_true",
                        help="儲存網頁 Diff 差異")
    args = parser.parse_args()

if __name__ == '__main__':
    main()