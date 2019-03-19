#! /usr/bin python3
# -*- coding:utf-8 -*-

#第二个例子：http://permit.mep.gov.cn/permitExt/outside/default.jsp
"""
许可信息公开：数据传输方式：get
General:
Request URL: http://permit.mep.gov.cn/permitExt/outside/Publicity?pageno=1
Request Method: GET
"""

import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

def get_one_page(pagenum):
    res = []
    url= 'http://permit.mep.gov.cn/permitExt/outside/Publicity?pageno={}'.format(pagenum)
    domain = 'http://permit.mep.gov.cn'
    webdata = requests.get(url)
    soup=BeautifulSoup(webdata.text,'lxml')
    table, = soup.select('table.tabtd')
    rows = table.select('tr')
    columns = [i.get_text() for i in rows[0].select('td')]
    for item in rows[1:]:
        data = [i.get_text().strip() for i in item.select('td')]
        data[-1] = domain + item.select('td')[-1].select('a')[0].get('href')
        res.append(data)

    print("LOG: {} page {} finished!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), pagenum))
    return pd.DataFrame(res, columns=columns)


def main():
    res=[]
    for i in range(1,21):
        res.append(get_one_page(i))
    df = pd.concat(res)
    df.to_excel('许可信息公开.xlsx',index=False)

if __name__ =='__main__':
    main()