#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/15 0015 18:54
# @Author  : KangQiang
# @File    : config.py
# @Software: PyCharm
import logging
import pymongo
from datetime import datetime, timedelta

# log settings
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('spider_log.log', mode='a', delay=False)
fh.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
fmt = "%(asctime)s %(levelname)s %(filename)s %(lineno)d %(message)s"
datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.89 Safari/537.36',
    'Connection': 'keep - alive',
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
}

test_ip_url = "http://wzzxbs.mofcom.gov.cn/WebProSP/app/infoPub/entpAudit"
REDIS_URL = "" # 负责ADSL通信的redis数据库地址
MONGO_URL = "" # 任务所在的MongoDB数据库地址

train_date = (datetime.now() + timedelta(days=5)).date()

format_url = "https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=" + str(
    train_date) + "&leftTicketDTO.from_station={from_station}&leftTicketDTO.to_station={to_station}&purpose_codes=ADULT"
path_stations_format_url = "https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={train_no}&from_station_telecode={from_station}&to_station_telecode={to_station}&depart_date=" + str(
    train_date)

client = pymongo.MongoClient(MONGO_URL)
db = client['crawler_task_status']
train_tasks_status_db = db["train_info_test"]
path_stations_tasks_status_db = db["path_stations_test"]
train_result_filename = "train_data.json"
path_stations_result_filename = "path_stations.json"
UN_PROCESSED = 0
PROCESSING = 1
PROCESSED = 2
ip_interval = 200
