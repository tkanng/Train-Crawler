#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/29 0029 18:30
# @Author  : KangQiang
# @File    : generateTaskDB.py
# @Software: PyCharm

from config import UN_PROCESSED, train_tasks_status_db,path_stations_tasks_status_db
from pymongo import InsertOne
import json
import re
import requests
import os

# train_list.js: 所有车次的始发站和终点站信息
# https://kyfw.12306.cn/otn/resources/js/query/train_list.js

# station_name.js: 所有车站的代码信息
# https://kyfw.12306.cn/otn/resources/js/framework/station_name.js

station_name_file = "station_name.temp"
train_list_file = "train_list.temp"
train_name_code = "train_name_code"
if not os.path.exists(station_name_file):
    station_name_url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    print("Downloading station_name_file")
    station_name_text = requests.get(station_name_url).text
    print("Downloading completed!")
    with open(station_name_file, "w", encoding="utf-8") as f:
        f.write(station_name_text)

if not os.path.exists(train_list_file):
    train_list_url = "https://kyfw.12306.cn/otn/resources/js/query/train_list.js"
    print("Downloading train_list_file")
    train_list_text = requests.get(train_list_url).text
    print("Downloading completed!")
    with open(train_list_file, "w", encoding="utf-8") as f:
        f.write(train_list_text)

station_name_code = {}
with open(station_name_file, "r",encoding="utf-8") as station_f:
    station_list = station_f.read().strip().split("@")[1:]
    for station in station_list:
        station_name_code[station.split("|")[1]] = station.split("|")[2]

pattern = re.compile(r'(\w+)\((\w+)-(\w+)\)')

with open(train_list_file, "r",encoding="utf-8") as train_f:
    s = train_f.read()
    data = json.loads(s[s.index("=")+1:])
    key = max(data.keys())
    train_list = []
    data = data[key]
    for train_type in data.keys():
        for train in data[train_type]:
            m = re.match(pattern, train["station_train_code"])
            if m:
                train_name = m.groups()[0]
                start_station = m.groups()[1]
                end_station = m.groups()[2]
                if start_station in station_name_code and end_station in station_name_code:
                    train_list.append(train_name + "\t" + start_station + "\t" + end_station + "\t"+train["train_no"] + "\t"
                              + station_name_code[start_station] + "\t" + station_name_code[end_station] + "\t"+"\n")
                else:
                    pass
                    # print(start_station + " " + end_station)
            else:
                pass
                # print(train["station_train_code"])

with open(train_name_code, "w", encoding="utf-8") as f:
    for t in train_list:
        f.write(t)


# 以任务url参数作为数据库primary key(1. 车次时刻表:起始站代码，终点站代码 2.车次经过站信息:起始站代码，终点站代码与train_no)
# 将 始发站代码-终点站代码 作为_id(注意：两个城市之间可能有多个车次，但_id只有一条关于始发站到终点站的记录)
train_ops = []
path_stations_ops = []
temp_set1 = set()
temp_set2 = set()
with open(train_name_code, 'r', encoding="utf-8") as f:
    for line in f.readlines():
        temp_set1.add(line.split("\t")[-3] + "-" + line.split("\t")[-2])
        temp_set2.add(line.split("\t")[-4] + "-" + line.split("\t")[-3] + "-" + line.split("\t")[-2])

for _id in temp_set1:
    train_ops.append(InsertOne({"_id": _id, "status": UN_PROCESSED}))
for _id in temp_set2:
    path_stations_ops.append(InsertOne({"_id": _id, "status": UN_PROCESSED}))

train_tasks_status_db.bulk_write(train_ops, ordered=False)
path_stations_tasks_status_db.bulk_write(path_stations_ops,ordered=False)

