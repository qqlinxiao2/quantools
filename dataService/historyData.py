# encoding: UTF-8

"""
本模块中主要包含：
1. 将MultiCharts导出的历史数据载入到MongoDB中用的函数
2. 将通达信导出的历史数据载入到MongoDB中的函数
3. 将交易开拓者导出的历史数据载入到MongoDB中的函数
4. 将OKEX下载的历史数据载入到MongoDB中的函数
"""

import csv
from datetime import datetime, timedelta
from time import time

import pymongo

# 数据库名称
from dataService.vtObject import VtBarData, VtTickData

SETTING_DB_NAME = 'VnTrader_Setting_Db'
POSITION_DB_NAME = 'VnTrader_Position_Db'

TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'
globalSetting = {'mongoHost':'192.168.27.19','mongoPort':27017}
#----------------------------------------------------------------------
def downloadEquityDailyBarts(self, symbol):
    """
    下载股票的日行情，symbol是股票代码
    """
    print('开始下载%s日行情' %symbol)
    
    # 查询数据库中已有数据的最后日期
    cl = self.dbClient[DAILY_DB_NAME][symbol]
    cx = cl.find(sort=[('datetime', pymongo.DESCENDING)])
    if cx.count():
        last = cx[0]
    else:
        last = ''
    # 开始下载数据
    import tushare as ts
    
    if last:
        start = last['date'][:4]+'-'+last['date'][4:6]+'-'+last['date'][6:]
        
    data = ts.get_k_data(symbol,start)
    
    if not data.empty:
        # 创建datetime索引
        self.dbClient[DAILY_DB_NAME][symbol].ensure_index([('datetime', pymongo.ASCENDING)], 
                                                            unique=True)                
        
        for index, d in data.iterrows():
            bar = VtBarData()
            bar.vtSymbol = symbol
            bar.symbol = symbol
            try:
                bar.open = d.get('open')
                bar.high = d.get('high')
                bar.low = d.get('low')
                bar.close = d.get('close')
                bar.date = d.get('date').replace('-', '')
                bar.time = ''
                bar.datetime = datetime.strptime(bar.date, '%Y%m%d')
                bar.volume = d.get('volume')
            except KeyError:
                print(d)
            
            flt = {'datetime': bar.datetime}
            self.dbClient[DAILY_DB_NAME][symbol].update_one(flt, {'$set':bar.__dict__}, upsert=True)            
        
        print('%s下载完成' %symbol)
    else:
        print('找不到合约%s' %symbol)

#----------------------------------------------------------------------
def loadMcCsv(fileName, dbName, symbol):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort']) 
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d['Open'])
        bar.high = float(d['High'])
        bar.low = float(d['Low'])
        bar.close = float(d['Close'])
        bar.date = datetime.strptime(d['Date'], '%Y-%m-%d').strftime('%Y%m%d')
        bar.time = d['Time']
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d['TotalVolume']

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print(bar.date, bar.time)
    
    print('插入完毕，耗时：%s' % (time()-start))

#----------------------------------------------------------------------
def loadTickCsv(fileName,symbol):
    """导入tick数据到Mongo数据库中"""
    import csv
    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' % (fileName, TICK_DB_NAME, symbol))
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[TICK_DB_NAME][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)
    # 读取数据和插入到数据库
    reader = csv.DictReader(open(fileName, 'r',encoding='gbk'))
    for d in reader:
        tick = VtTickData()
        # 代码相关
        tick.gatewayName = 'CTP'
        tick.symbol = symbol  # 合约代码
        tick.exchange = d['市场代码']  # 交易所代码
        tick.vtSymbol = symbol  # 合约在vt系统中的唯一代码，通常是 合约代码.交易所代码
        """
        #市场代码, 1合约代码, 2时间, 3最新, 4持仓, 5增仓, 6成交额, 7成交量, 8开仓, 9平仓, 
        #10成交类型, 11方向, 12买一价, 13卖一价, 14买一量, 15卖一量
        """
        # 成交数据
        tick.lastPrice = float(d['最新'])  # 最新成交价
        tick.lastVolume = d['增仓']  # 最新成交量
        tick.volume = d['成交量']  # 今天总成交量
        tick.openInterest = d['持仓']  # 持仓量
        tick.datetime = datetime.strptime(d['时间'], '%Y-%m-%d %H:%M:%S.%f')  # python的datetime时间对象
        tick.time = tick.datetime.strftime('%H:%M:%S.%f')  # 时间 11:20:56.5
        tick.date = tick.datetime.strftime('%Y%m%d')  # 日期 20151009
        # 常规行情
        tick.openPrice = 0.0  # 今日开盘价
        tick.highPrice = 0.0  # 今日最高价
        tick.lowPrice = 0.0  # 今日最低价
        tick.preClosePrice = 0.0

        tick.upperLimit = 0.0  # 涨停价
        tick.lowerLimit = 0.0  # 跌停价

        # 五档行情
        tick.bidPrice1 = float(d['买一价'])
        tick.askPrice1 = float(d['卖一价'])
        tick.bidVolume1 = d['买一量']
        tick.askVolume1 = d['卖一量']
        flt = {'datetime': tick.datetime}
        collection.update_one(flt, {'$set': tick.__dict__}, upsert=True)
        print(tick.date, tick.time)

    print('插入完毕，耗时：%s' % (time() - start))
#----------------------------------------------------------------------
def loadTbCsv(fileName, dbName, symbol):
    """将TradeBlazer导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[1])
        bar.high = float(d[2])
        bar.low = float(d[3])
        bar.close = float(d[4])
        bar.date = datetime.strptime(d[0].split(' ')[0], '%Y/%m/%d').strftime('%Y%m%d')
        bar.time = d[0].split(' ')[1]+":00"
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[5]
        bar.openInterest = d[6]

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print(bar.date, bar.time)
    
    print('插入完毕，耗时：%s' % (time()-start))
    
 #----------------------------------------------------------------------
def loadTbPlusCsv(fileName, dbName, symbol):
    """将TB极速版导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv    

    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)      

    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[2])
        bar.high = float(d[3])
        bar.low = float(d[4])
        bar.close = float(d[5])
        bar.date = str(d[0])
        
        tempstr=str(round(float(d[1])*10000)).split(".")[0].zfill(4)
        bar.time = tempstr[:2]+":"+tempstr[2:4]+":00"
        
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[6]
        bar.openInterest = d[7]
        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print(bar.date, bar.time)

    print('插入完毕，耗时：%s' % (time()-start))

#----------------------------------------------------------------------
def loadTdxCsv(fileName, dbName, symbol):
    """将通达信导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    import csv
    
    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))
    
    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)   
    
    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName, 'r'))
    for d in reader:
        bar = VtBarData()
        bar.vtSymbol = symbol
        bar.symbol = symbol
        bar.open = float(d[2])
        bar.high = float(d[3])
        bar.low = float(d[4])
        bar.close = float(d[5])
        bar.date = datetime.strptime(d[0], '%Y/%m/%d').strftime('%Y%m%d')
        bar.time = d[1][:2]+':'+d[1][2:4]+':00'
        bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
        bar.volume = d[6]
        bar.openInterest = d[7]

        flt = {'datetime': bar.datetime}
        collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)  
        print(bar.date, bar.time)
    
    print('插入完毕，耗时：%s' % (time()-start))

#----------------------------------------------------------------------
def loadOKEXCsv(fileName, dbName, symbol):
    """将OKEX导出的csv格式的历史分钟数据插入到Mongo数据库中"""
    start = time()
    print('开始读取CSV文件%s中的数据插入到%s的%s中' %(fileName, dbName, symbol))

    # 锁定集合，并创建索引
    client = pymongo.MongoClient(globalSetting['mongoHost'], globalSetting['mongoPort'])
    collection = client[dbName][symbol]
    collection.ensure_index([('datetime', pymongo.ASCENDING)], unique=True)

    # 读取数据和插入到数据库
    reader = csv.reader(open(fileName,"r"))
    for d in reader:
        if len(d[1]) > 10:
            bar = VtBarData()
            bar.vtSymbol = symbol
            bar.symbol = symbol

            bar.datetime = datetime.strptime(d[1], '%Y-%m-%d %H:%M:%S')
            bar.date = bar.datetime.date().strftime('%Y%m%d')
            bar.time = bar.datetime.time().strftime('%H:%M:%S')

            bar.open = float(d[2])
            bar.high = float(d[3])
            bar.low = float(d[4])
            bar.close = float(d[5])

            bar.volume = float(d[6])
            bar.tobtcvolume = float(d[7])

            flt = {'datetime': bar.datetime}
            collection.update_one(flt, {'$set':bar.__dict__}, upsert=True)
            print('%s \t %s' % (bar.date, bar.time))

    print('插入完毕，耗时：%s' % (time()-start))
    
