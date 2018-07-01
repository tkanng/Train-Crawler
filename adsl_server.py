#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/6 0006 20:46
# @Author  : KangQiang
# @File    : server.py
# @Software: PyCharm
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/6 0006 20:46
# @Author  : KangQiang
# @File    : server.py
# @Software: PyCharm
import commands
import redis
import re
import time
import datetime
import logging

# log settings
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('adsl_log.log', mode='a', delay=False)
fh.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
fmt = "%(asctime)s %(lineno)d %(message)s"
datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)

REDIS_URL = '' # 与爬虫服务器进行通信的redis地址。
time_delta = datetime.timedelta(seconds=90)


# ADSL server
def get_ip():
    (status, output) = commands.getstatusoutput('ifconfig')
    if status == 0:
        m = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)\W+P-t-P", output)
        ip = str(m.group(1))
        return ip
    else:
        print('cannot get ip! And the output is ', output)
        logger.info('cannot get ip! And the output is {}'.format(str(output)))


# ADSL server code
if __name__ == '__main__':
    basic_redis = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)
    count = 0
    pre_ip = get_ip()
    print("pre_ip: " + pre_ip)
    while True:
        time.sleep(2)
        count += 1
        if count % 46 == 0:
            if pre_ip == get_ip():  # 至少90s之后ip相同,说明陷入了异常
                logger.error("Ip has not changed for 90s.")
                while True:  # 一直运行指导adsl-stop 和adsl-start命令执行成功
                    try:
                        # disconnect这个client，防止redis服务器的客户端太多
                        basic_redis.connection_pool.disconnect()

                        status1,output1 = commands.getstatusoutput('adsl-stop')
                        time.sleep(0.1)
                        status2, output2 = commands.getstatusoutput('adsl-start')
                        if status1 == 0 and status2 == 0:
                            basic_redis = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)
                            now_ip = get_ip()
                            if now_ip == basic_redis.get('ip'):
                                continue
                            basic_redis.set('ip', now_ip)
                            basic_redis.set('change_ip', '0')
                            logger.info('Processing Exception Successfully!')
                            break
                        logger.info('Retry to change ip')

                    except Exception as e:
                        logger.error(str(e))
                        pass

            count = 1
            pre_ip = get_ip()  # 记录上一次循环结束后的ip

        if count % 15 == 0:
            logger.info('')

        try:
            if basic_redis.get('change_ip') == '1':
                print("change_ip == 1")
                while True:
                    # disconnect这个client，防止redis服务器的客户端太多
                    basic_redis.connection_pool.disconnect()

                    status1, output1 = commands.getstatusoutput('adsl-stop')
                    status2, output2 = commands.getstatusoutput('adsl-start')
                    logger.info('status1:{status1} status2:{status2}'.format(status1=status1, status2=status2))

                    if status1 == 0 and status2 == 0:
                        print("status==0")
                        now_ip = get_ip()
                        # Reconnect redis server. cannot ignore the step ！！
                        basic_redis = redis.Redis.from_url(REDIS_URL, db=1, decode_responses=True)
                        if basic_redis.get('ip') == now_ip:
                            continue
                        basic_redis.set('ip', now_ip)
                        basic_redis.set('change_ip', '0')  # reset the flag
                        logger.info('Succeed! Present IP:{now_ip}'.format(now_ip=now_ip))
                        break
                    else:
                        logger.error('ADSL failed to start.')
                        time.sleep(1)
                        continue
        except Exception as e:
            logger.error(str(e))
            pass
