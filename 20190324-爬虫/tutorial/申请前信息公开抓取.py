#第一个例子：http://permit.mep.gov.cn/permitExt/outside/default.jsp
"""
申请前信息公开：数据传输方式：post
General:
Request URL: http://permit.mep.gov.cn/permitExt/syssb/xxgk/xxgk!sqqlist.action
Request Method: POST

FormData:
page.pageNo=1&page.orderBy=&page.order=&province=&city=&registerentername=&searchFbTime=&inPageNo=17
"""

import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

def get_one_page(pagenum):
    """
    得到某一页的数据
    :param int pagenum: 需要抓取的页数
    :return list:
    """
    res=[]
    url ='http://permit.mep.gov.cn/permitExt/syssb/xxgk/xxgk!sqqlist.action'
    domain ='http://permit.mep.gov.cn'
    params = 'page.pageNo={}&page.orderBy=&page.order=&province=&city=&registerentername=&searchFbTime=&inPageNo=1'.format(pagenum)
    webdata = requests.post(url,data=params)
    soup = BeautifulSoup(webdata.text,'lxml')

    table, = soup.select('table.tabtd')
    rows = table.select('tr')
    columns = [i.get_text() for i in rows[0].select('td')]
    for item in rows[1:]:
        data = [i.get_text().strip() for i in item.select('td')]
        data[-2]=domain+item.select('td')[-2].select('a')[0].get('href')
        res.append(data)


    print("LOG: {} page {} finished!".format(time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),pagenum))
    return pd.DataFrame(res,columns=columns)

def main():
    res=[]
    for i in range(1,18):
        res.append(get_one_page(i))
    df = pd.concat(res)
    df.to_excel('申请前信息公开.xlsx',index=False)

if __name__ =='__main__':
    main()