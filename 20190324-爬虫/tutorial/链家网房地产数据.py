#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# __author__ = "Brady Hu"
# __date__ = "20180326"
import pprint

import requests
from requests import RequestException
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
import os
proxy=False
frequency = 5
#代理工具和请求工具(req,get_proxy)
def req(url):
    headers = {"User_Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"}
    while True:
        try:
            webdata  = requests.get(url,headers=headers,proxies=get_proxy(),timeout = 5)
            time.sleep(frequency)
            if webdata.status_code == 200:
                return webdata
            else:
                pass
        except RequestException as e:
            print(e.args)

def get_proxy():
    """
    返回None或形如{"https":"https://127.0.0.1"}的代理
    :return:
    """
    if not proxy:
        return None
    else:
        url = 'http://api.ip.data5u.com/dynamic/get.html?order=44b365bd1275e9f6a0d15b720526f4d4&sep=3'
        while True:
            try:
                webdata = requests.get(url)
                time.sleep(1)
                if webdata.status_code == 200:
                    return {"https":"https://{}".format(webdata.text.strip())}
                else:
                    pass
            except RequestException:
                pass
#抓取区域信息(get_area,get_area_1)
def get_area():
    """
    抓取区域列表
    :return: list
    """
    res=[]
    url = 'https://sz.lianjia.com/xiaoqu/'
    domain = 'https://sz.lianjia.com'
    webdata = req(url)
    soup = BeautifulSoup(webdata.text,'lxml')
    areas = soup.select('div.position dl dd div a')
    for area,url_ in  [[i.get_text(),domain+i.get('href')] for i in areas]:
        print(url_)
        res.extend(get_area_1(url_))
    return res

def get_area_1(url):
    #得到某个大区下面各个小区域
    domain = 'https://sz.lianjia.com'
    webdata = req(url)
    soup = BeautifulSoup(webdata.text, 'lxml')
    areas = soup.select('div.position dl dd > div > div:nth-of-type(2) a')
    res = [[i.get_text(), domain + i.get('href')] for i in areas]
    pprint.pprint(res)
    return res
#抓取小区列表
def get_xiaoqu(areas):
    """
    抓取小区
    :param areas:dict()
    :return:dict()
    """
    res = []
    for area,url in areas:
        #得到某个区域下面的所有小区
        webdata = req(url)
        soup = BeautifulSoup(webdata.text,'lxml')
        total = soup.select('h2.total span')[0].get_text()
        pages = round((int(total)-1)/30)+1
        for pageno in range(1,pages+1):
            tmp=[]
            url_=url+'pg{}/'.format(pageno)
            webdata_ = req(url_)
            soup_ = BeautifulSoup(webdata_.text,'lxml')
            xiaoqus = soup_.select('div.content ul.listContent li')
            for xiaoqu in xiaoqus:
                title = xiaoqu.select('div.info div.title')[0].get_text().strip()
                xiaoquurl = xiaoqu.select('div.info div.title a')[0].get('href')
                houseInfo = xiaoqu.select('div.info div.houseInfo')[0].get_text()
                positionInfo = xiaoqu.select('div.info div.positionInfo')[0].get_text()
                positionInfo = "".join(positionInfo.split())
                tagList = [i.get_text() for i in xiaoqu.select('div.info div.tagList span')]
                price = xiaoqu.select('div.xiaoquListItemPrice span')[0].get_text()
                sellCount = xiaoqu.select('div.xiaoquListItemSellCount a span')[0].get_text()
                data = {'title':title,
                        'url':xiaoquurl,
                        'houseInfo':houseInfo,
                        'positionInfo':positionInfo,
                        'tagList':tagList,
                        'price':price,
                        'sellCount':sellCount}
                print(data)
                tmp.append(data)
            res.extend(tmp)
        print(area,'finished!')
    return res

def crawl_xiaoqu():
    print("LOG: {} start crawl xiaoqu!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    areas=get_area()
    xiaoqulist  = get_xiaoqu(areas)
    df = pd.DataFrame(xiaoqulist)
    df.to_excel('小区信息.xlsx')
    print("LOG: {} finish crawl xiaoqu!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
#抓取各小区详细信息
def crawl_xiaoqu_info():
    xiaoqu = pd.read_excel('小区信息.xlsx')
    for index, item in xiaoqu.iterrows():
        if os.path.exists("xiaoqu/{}.xlsx".format(item['title'])):
            continue
        else:
            print("LOG: {} xiaoqu {} start!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), item['title']))
            crawl_one_xiaoqu(item)
            print("LOG: {} xiaoqu {} finished!".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), item['title']))

def crawl_one_xiaoqu(xiaoquinfo):
    """
    分别对：
    https://sz.lianjia.com/xiaoqu/2411048738974/
    https://sz.lianjia.com/ershoufang/c2411048738974/
    https://sz.lianjia.com/chengjiao/c2411048738974/
    https://sz.lianjia.com/zufang/c2411048738974/
    进行抓取，并保存到同一个excel中
    """
    Writer = pd.ExcelWriter('xiaoqu/{}.xlsx'.format(xiaoquinfo['title']))

    basic = {}
    url_basic = xiaoquinfo['url']
    webdata = req(url_basic)
    soup= BeautifulSoup(webdata.text,'lxml')
    if soup.select('div.xiaoquPrice span.xiaoquUnitPrice'):
        price = soup.select('div.xiaoquPrice span.xiaoquUnitPrice')[0].get_text()
    else:
        price = None
    basic['price']=price
    for item in soup.select('div.xiaoquInfoItem'):
        basic[item.select('span.xiaoquInfoLabel')[0].get_text()]=item.select('span.xiaoquInfoContent')[0].get_text()
    bdlnglat = re.compile("resblockPosition:'(.*?),(.*?)'").findall(webdata.text)[0]
    basic['bdlnglat']=bdlnglat
    print(basic)
    pd.DataFrame([basic]).to_excel(Writer,'basic')

    #二手房
    url_ershoufang = xiaoquinfo['url'].replace('xiaoqu/','ershoufang/c')
    ershoufang = []
    webdata = req(url_ershoufang)
    soup = BeautifulSoup(webdata.text, 'lxml')
    total = soup.select('.total span')[0].get_text()
    pages = round((int(total) - 1) / 30) + 1
    for pageno in range(1,pages+1):
        url= url_ershoufang.replace('ershoufang/c','ershoufang/pg{}c'.format(pageno))
        webdata = req(url)
        soup = BeautifulSoup(webdata.text, 'lxml')
        for item in soup.select('ul.sellListContent li div.info'):
            title= item.select('div.title')[0].get_text()
            url = item.select('div.title')[0].get('href')
            address = item.select('div.address')[0].get_text()
            flood = item.select('div.flood')[0].get_text()
            followInfo = item.select('div.followInfo')[0].get_text()
            tag = [i.get_text() for i in item.select('div.tag span')]
            priceInfo =[item.select('div.totalPrice span')[0].get_text(),
                        item.select('div.unitPrice span')[0].get_text()]
            data = {'title':title,
                    'url':url,
                    'address':address,
                    'flood':flood,
                    'followInfo':followInfo,
                    'tag':tag,
                    'priceInfo':priceInfo}
            ershoufang.append(data)
    pprint.pprint(ershoufang)
    pd.DataFrame(ershoufang).to_excel(Writer,'ershoufang')

    #成交
    url_chengjiao = xiaoquinfo['url'].replace('xiaoqu/', 'chengjiao/c')
    chengjiao=[]
    webdata = req(url_chengjiao)
    soup = BeautifulSoup(webdata.text, 'lxml')
    total = soup.select('.total span')[0].get_text()
    pages = round((int(total) - 1) / 30) + 1
    for pageno in range(1, pages + 1):
        url = url_chengjiao.replace('chengjiao/c', 'chengjiao/pg{}c'.format(pageno))
        webdata = req(url)
        soup = BeautifulSoup(webdata.text, 'lxml')
        for item in soup.select('ul.listContent li div.info'):
            title = item.select('div.title')[0].get_text()
            url = item.select('div.title')[0].get('href')
            houseInfo = item.select('div.address div.houseInfo')[0].get_text()
            dealDate = item.select('div.address div.dealDate')[0].get_text()
            totalPrice = item.select('div.address div.totalPrice')[0].get_text()

            positionInfo = item.select('div.flood div.positionInfo')[0].get_text()
            source = item.select('div.flood div.source')[0].get_text()
            unitPrice = item.select('div.flood div.unitPrice')[0].get_text()
            dealHouseInfo =[i.get_text() for i in item.select('div.dealHouseInfo span.dealHouseTxt span')]
            dealCycleInfo = [i.get_text() for i in item.select('span.dealCycleTxt span')]
            data = {'title': title,
                    'url':url,
                    'houseInfo':houseInfo,
                    'dealDate':dealDate,
                    'totalPrice':totalPrice,
                    'positionInfo':positionInfo,
                    'source':source,
                    'unitPrice':unitPrice,
                    'dealHouseInfo':dealHouseInfo,
                    'dealCycleInfo':dealCycleInfo}
            chengjiao.append(data)
    pprint.pprint(chengjiao)
    pd.DataFrame(chengjiao).to_excel(Writer, 'chengjiao')

    #租房
    url_zufang = xiaoquinfo['url'].replace('xiaoqu/', 'zufang/c')
    zufang =[]
    webdata = req(url_zufang)
    soup = BeautifulSoup(webdata.text, 'lxml')
    total = soup.select('h2 > span')[0].get_text()
    pages = round((int(total) - 1) / 30) + 1
    for pageno in range(1,pages+1):
        url = url_zufang+'pg{}/'.format(pageno)
        webdata = req(url)
        soup = BeautifulSoup(webdata.text,'lxml')
        for item in soup.select('ul.house-lst li div.info-panel'):
            title = item.select('h2 a')[0].get_text()
            url = item.select('h2 a')[0].get('href')
            where =item.select('div.where')[0].get_text()
            other = item.select('div.other')[0].get_text()
            chanquan = [i.get_text() for i in item.select('div.chanquan div span span')]
            price = item.select('div.price span')[0].get_text()
            price_pre = item.select('div.price-pre')[0].get_text()
            square = item.select('div.square div span')[0].get_text()
            data = {'title':title,
                    'url':url,
                    'where':where,
                    'other':other,
                    'chanquan':chanquan,
                    'price':price,
                    'price_pre':price_pre,
                    'square':square}
            zufang.append(data)
    pprint.pprint(zufang)
    pd.DataFrame(zufang).to_excel(Writer,'zufang')

    Writer.close()
#合并得到完整数据
def merge_data():
    sheets = ['basic', 'ershoufang', 'chengjiao', 'zufang']
    for sheet in sheets:
        dfs = []
        for item in os.listdir('xiaoqu'):
            dfs.append(pd.read_excel('xiaoqu/' + item, sheetname=sheet))
        res = pd.concat(dfs)
        res.to_excel(sheet + '.xlsx',index=False)

if __name__=='__main__':
    crawl_xiaoqu()
    # crawl_xiaoqu_info()
    # merge_data()