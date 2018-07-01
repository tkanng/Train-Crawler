#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/30 0030 16:48
# @Author  : KangQiang
# @File    : pathStationCrawler.py
# @Software: PyCharm

import json
import threading
import time
from queue import Queue
from config import *
from pymongo import UpdateOne
from get_page import get_page, get_count

task_queue = Queue()
response_queue = Queue()
format_url = path_stations_format_url
tasks_status_db = path_stations_tasks_status_db
result_filename = path_stations_result_filename


def parse(html_response):
    '''
    将 get_page 得到的 response.text 解析，得到其中有用的数据
    :param html_response:
    :return: list。停靠站信息
     '''
    data = json.loads(html_response)["data"]["data"]
    return data


def construct_url(url_paras):
    '''
    根据url_paras构造页面网址
    :param url_paras: 字符串。以'-'分割不同参数
    :return: 网址。需要注意的是，网址中有train_date参数。train_date:选择程序运行时刻的后5天。
    '''
    return format_url.format(train_no=url_paras.split("-")[0], from_station=url_paras.split("-")[1],
                             to_station=url_paras.split("-")[2])


class Crawler(threading.Thread):
    '''
    数据抓取类
    '''

    def __init__(self, task_status_db, parse_fun, construct_url_fun):
        '''
        :param collection: 数据库。任务相关数据库，记录了任务抓取状态。以url_para作为primary key
        :param parse_fun: 函数。解析response.text，返回有用数据。
        :param task_url_fun: 函数。利用task_queue中的数据，得到task_url。
        '''
        super(Crawler, self).__init__()
        self.collection = task_status_db
        self.parse = parse_fun
        self.construct_url = construct_url_fun

    def run(self):
        global task_queue
        global response_queue
        while True:
            url_paras = task_queue.get()
            task_url = self.construct_url(url_paras)
            try:
                # 这里的 requests需要包装起来
                response = get_page(task_url)
                if response:
                    data = self.parse(response)
                    if data is not None:  # 如果为None，表明解析response.text出现错误。
                        response_queue.put((data, url_paras))
                    else:
                        self.collection.update_one({'_id': url_paras}, update={'$set': {'status': UN_PROCESSED}})
                else:
                    # 把数据库中的 status重新置为 UN_PROCESSED
                    self.collection.update_one({'_id': url_paras}, update={'$set': {'status': UN_PROCESSED}})
            except Exception as e:
                logger.critical('In Crawler:{}'.format(str(e)) + str(task_url))
                self.collection.update_one({'_id': url_paras}, update={'$set': {'status': UN_PROCESSED}})
                pass


class TaskProducer(threading.Thread):
    def __init__(self, task_status_db):
        super(TaskProducer, self).__init__()
        self.collection = task_status_db

    def run(self):
        global task_queue
        while True:
            try:
                if task_queue.qsize() < 300:
                    temp = self.collection.find({'status': UN_PROCESSED}, limit=60)
                    for single_item in temp:
                        # 设置为PROCESSING
                        self.collection.update_one({'_id': single_item['_id']},
                                                   update={'$set': {'status': PROCESSING}})
                        task_queue.put(single_item['_id'])
                else:
                    time.sleep(3)
            except Exception as e:
                logger.critical('In Task1Producer:{}'.format(str(e)))
                pass


class DataSaver3(threading.Thread):
    def __init__(self, task_status_db, file_name):
        '''

        :param task_status_db: 记录任务状态的数据库
        :param data_db: 数据存储的数据库。
        :param file_name: 数据存储的文件名。
        '''
        super(DataSaver3, self).__init__()
        self.status_db = task_status_db
        self.file_name = file_name

    def save2db(self, size):
        '''
        :param size: response_size
        :return:
        '''
        global response_queue
        ops = []  # users_info需要执行的运算操作
        try:
            for _ in range(size):
                data, url_paras = response_queue.get()  # 一个界面的response
                ops.append(
                    UpdateOne({'_id': url_paras}, update={'$set': {'status': PROCESSED, 'data': data}}))

                # self.status_db.update_one({'_id': recordId}, {'$set': {'status': PROCESSED, 'data': data}})
            if ops:
                self.status_db.bulk_write(ops, ordered=False)
        except Exception as e:
            if 'batch op errors occurred' not in str(e):
                logger.error('In save2db:' + str(e))
            pass

    def save2file(self, size):
        '''
        将size大小的response解析之后存入本地文件
        :param size: response_size
        :return:
        '''
        global response_queue
        with open(self.file_name, 'a', encoding="utf-8") as f:
            for _ in range(size):
                try:
                    data, url_para = response_queue.get()
                    self.status_db.find_one_and_update({'_id': url_para},
                                                       {'$set': {'status': PROCESSED}})  # 将相应的uid置为PROCESSED
                    f.write(json.dumps({"_id": url_para, "data": data}) + '\n')
                except Exception as e:
                    logger.error('In save2file:' + str(e))
                    pass

    def run(self):
        while True:
            self.save2db(30)
            # self.save2file(200)


class Supervisor(threading.Thread):
    def __init__(self, tasks_status_db):
        super(Supervisor, self).__init__()
        self.tasks_status_db = tasks_status_db

    def run(self):
        global response_queue
        while True:
            pre_count = get_count()
            time.sleep(10)
            now_count = get_count()
            logger.info('page_count:{now_count} speed:{speed} response_queue.qsize():{size}'.format(now_count=now_count,
                                                                                                    speed=(
                                                                                                              now_count - pre_count) / 10,
                                                                                                    size=response_queue.qsize()))
            print("PROCESSED: " + str(self.tasks_status_db.find({"status": PROCESSED}).count()))
            print("PROCESSING: " + str(self.tasks_status_db.find({"status": PROCESSING}).count()))
            print("UN_PROCESSED: " + str(self.tasks_status_db.find({"status": UN_PROCESSED}).count()))


if __name__ == '__main__':
    t = TaskProducer(tasks_status_db)
    t.start()

    t = DataSaver3(tasks_status_db, result_filename)
    t.start()
    for i in range(2):
        t = Crawler(tasks_status_db, parse, construct_url)
        t.start()

    t = Supervisor(path_stations_tasks_status_db)
    t.start()
