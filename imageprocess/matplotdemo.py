# encoding: UTF-8
from collections import deque
from queue import Queue

import matplotlib.pyplot as plt
import csv
import numpy as np
import matplotlib.dates as mdates
from matplotlib import ticker
import csv
from datetime import datetime

N = 0
date = []
price = []
pointList = []
class Point(object):
    def __init__(self,date,price,direction):
        self.date = date
        self.price = price
        self.direction = direction

def loadTickCsvAsNumpy(fileName):
    # return np.loadtxt(fileName, dtype=float, skiprows=1, converters={2:mdates.strpdate2num('%Y-%m-%d %H:%M:%S.%f')},
                        #comments='#', delimiter=',',usecols=(2, 3), unpack=True)
    reader = csv.DictReader(open(fileName, 'r',encoding='gbk'))
    for d in reader:
        p = int(d['最新'])
        t = datetime.strptime(d['时间'], '%Y-%m-%d %H:%M:%S.%f')
        if (t.hour >= 21 and t.hour <=23) or (t.hour >= 9 and t.hour <=15):
            price.append(p)
            date.append(t)

def format_date(x, pos=None):
    #保证下标不越界,很重要,越界会导致最终plot坐标轴label无显示
    thisind = np.clip(int(x+0.5), 0, len(date)-1)
    return date[thisind].strftime('%H:%M:%S')

def drawImage(date,price):
    ind = np.arange(len(date))
    fig = plt.figure()
    fig.suptitle('figure title demo', fontsize=14, fontweight='bold')
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title("axes title")
    ax.set_xlabel("x label")
    ax.set_ylabel("y label")
    #ax.xaxis.set_major_locator(mdates.HourLocator())
    #ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    for point in pointList:
        #plt.text(key, value, 'this', ha='center', va='bottom', fontsize=7)
        if point.direction:
            plt.annotate('buy', xy=(point.date, point.price), xytext=(point.date, point.price-10),
                        arrowprops=dict(facecolor='red',arrowstyle='->'))
        else:
            plt.annotate('sell', xy=(point.date, point.price), xytext=(point.date, point.price+10),
                         arrowprops=dict(facecolor='green', arrowstyle='->'))
    plt.plot(ind, price)
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    fig.autofmt_xdate()
    plt.show()

def timeWindoAanalysis(timeSpace,scope):
    if len(date) != len(price):
        return
    queue = deque()
    for i in range(len(date)):
        #时间窗队列操作
        if queue.__len__() == 0:
            queue.append(i)
        else:
            index = queue.popleft()
            if date[i].timestamp() - date[index].timestamp() > timeSpace:
                #有效时间窗 替换
                queue.append(i)
            else:
                #无效时间窗 插入
                queue.appendleft(index)
                queue.append(i)
            #动量判断
            left = queue.popleft()
            right = queue.pop()
            queue.appendleft(left)
            queue.append(right)
            sub = price[right] - price[left]
            if abs(sub) >= scope:
                print(date[right],sub)
                pointList.append(Point(right,price[right],sub > 0))
                queue.clear()




if __name__ == '__main__':
    #加载数据
    loadTickCsvAsNumpy('P:\Work\quant\m\m主力连续_20180323.csv')
    #分析
    timeWindoAanalysis(5,3)
    #画图
    drawImage(date,price)

    # t = datetime.strptime('2018-03-22 21:00:00.379', '%Y-%m-%d %H:%M:%S.%f')
    # t2 = datetime.strptime('2018-03-22 21:00:01.879', '%Y-%m-%d %H:%M:%S.%f')
    # print(t2.timestamp()-t.timestamp())