#!/usr/bin/env python3

import MySQLdb
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class FloodfireDiff():
    # 列出各新聞的版別黑名單，以key=source_id, value=版別方式呈現
    # 1=蘋果日報, 2=中時電子報, 3=中央社, 4=ETtoday, 5=自由時報, 6=新頭殼, 7=nownews, 8=聯合新聞網
    black_list = {
        1: ["3C","時尚","副刊","動物","地產","壹週刊","特企","車市","辣蘋道"],
        2: ["旅遊","軍事"],
        3: [],
        4: ["時尚","旅遊","3C家電","ET來了","ET車雲","保險","公益","名家","寵物動物","房產雲","探索","新奇","法律","消費","男女","直銷雲","網搜","親子","軍武","遊戲","運勢","電影","電競"],
        5: ["3c","3C","auto","istyle","partners","playing","時尚","汽車","玩咖","英文"],
        6: [],
        7: [],
        8: ["閱讀"],
        9: [],
        10: [],
        11: [],
        12: [],
        13: [],
        14: [],
        15: [],
        16: [],
        17: [],
        18: []
    }
    compared_cols = ['publish_time', 'title', 'body', 'authors', 'image', 'video']

    def page_diff(self, page1, page2):
        diff_col_list = []
        for compared_col in self.compared_cols:
            if compared_col in page1 and compared_col in page2:
                now_value = str(page1[compared_col]) if compared_col not in ['authors', 'keywords'] else ','.join(page1[compared_col])
                last_value = str(page2[compared_col])
                if now_value != last_value:
                    # 兩個都有該項目，但兩者不同，所以Diff
                    diff_col_list.append(compared_col)
                else:
                    # 兩個都有該項目，但兩者相同，所以沒有Diff
                    pass
            elif compared_col not in page1 and compared_col not in page2:
                # 兩個都沒有該項目，因此沒有Diff
                pass
            else:
                # 其中一個有該項目，所以有Diff
                diff_col_list.append(compared_col)
        if len(diff_col_list) == 0:
            return None
        else:
            return diff_col_list
