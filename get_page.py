#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/31 0031 15:22
# @Author  : KangQiang
# @File    : get_page.py
# @Software: PyCharm
# 返回网页的文本
import random
import threading
import time
import redis
import requests
from config import logger, REDIS_URL, headers, test_ip_url, ip_interval
# 可实现不停切换Ip

timeout = 15  # 访问网页的超时时间
changing_ip_flag = True
correct_page_count = 0


# 改变ip，并返回
def change_get_ip():
    basic_redis = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)
    pre_ip = basic_redis.get('ip')
    basic_redis.set('change_ip', 1)
    while pre_ip == basic_redis.get('ip'):  # Wait until adsl server get a new ip successfully.
        time.sleep(1)
    return basic_redis.get('ip')


# 验证ip，并返回一个有效的ip
def get_valid_ip():
    temp_ip = ''
    for _ in range(6):
        temp_ip = change_get_ip()  # adsl已经成功切换ip，需要在爬虫服务器上验证该ip是否可用
        try:
            requests.get(test_ip_url, headers=headers, timeout=7, proxies={'https': 'https://' + temp_ip + ':3128'})
        except Exception as e:
            if 'Caused by ConnectTimeoutError' in str(e) or 'Max retries exceeded' in str(e):
                logger.info('Invalid ip:{}'.format(temp_ip))
                continue
            else:
                logger.info('Error In get_valid_ip:{}'.format(str(e)))
                continue
        else:
            logger.info('Valid ip:{}'.format(str(temp_ip)))
        break
    return temp_ip


# 封装改变ip的函数,便于IpChanger()使用
def change_ip():
    global ip
    ip = get_valid_ip()


def ip_flag(value):
    global changing_ip_flag
    changing_ip_flag = value


def get_count():
    global correct_page_count
    return correct_page_count


def get_ip():
    global ip
    return ip


def get_page(url):
    '''
    :param url:
    :return:
    '''
    global ip
    global changing_ip_flag
    global correct_page_count
    try:
        if changing_ip_flag:
            # 表示正在切换ip
            time.sleep(random.randint(1, 5))
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.get(url, headers=headers, timeout=timeout, proxies={'https': 'https://' + ip + ':3128'})

        if response.status_code == 200:
            correct_page_count += 1
            return response.text
        else:
            return None
    except Exception as e:
        if 'Cannot connect to proxy' in str(e):
            return None
        elif 'Caused by ConnectTimeoutError' in str(e):
            return None
        elif 'read timeout' in str(e) or 'Read timed out' in str(e):
            return None
        else:
            logger.error("In get page exception: ".format(str(e)))
            return None


def post_page(url, data):
    '''
    :param url: 地址
    :param data: post的数据
    :return:
    '''
    global ip
    global changing_ip_flag
    global correct_page_count
    try:
        if changing_ip_flag:
            # 表示正在切换ip
            time.sleep(random.randint(1, 4))
            response = requests.post(url, headers=headers, timeout=timeout, data=data)
        else:
            response = requests.post(url, headers=headers, timeout=timeout, data=data,
                                     proxies={'https': 'https://' + ip + ':3128'})

        if response.status_code == 200:
            correct_page_count += 1
            return response.text
        else:
            return None
    except Exception as e:
        if 'Cannot connect to proxy' in str(e):
            return None
        elif 'Caused by ConnectTimeoutError' in str(e):
            return None
        elif 'read timeout' in str(e) or 'Read timed out' in str(e):
            return None
        else:
            logger.error("In get page exception: ".format(str(e)))
            return None


# 每隔ip_interval切换一次ip
class IpChanger(threading.Thread):
    def __init__(self):
        super(IpChanger, self).__init__()

    def run(self):
        while True:
            time.sleep(ip_interval)
            logger.info('Change Ip')
            ip_flag(True)  # 在改变ip的过程中将flag置为True,让爬虫不使用代理访问网页
            change_ip()
            ip_flag(False)  # 得到有效的ip后，将flag置为False,让爬虫重新使用代理访问网页

#
# change_ip()
# logger.info('Initial ip:{}'.format(ip))
# t = IpChanger()
# t.start()
