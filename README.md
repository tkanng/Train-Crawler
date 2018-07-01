#### 1. 基本介绍： 

- `config.py`：配置信息文件

- `generate_task2db.py`:从12306网站上下载`train_list`和`station_name`信息，对数据进行初步处理。生成两类任务：车次时刻表信息抓取任务(`train_crawler.py`)与车次经停靠站点信息（`path_stations_crawler.py`）。`_id`（主键）：任务抓取url参数。车次时刻表信息抓取任务，对应起始站代码和终点站代码；车次经停靠站点信息抓取任务，对应车次序号`train_no`、起始站代码和终点站代码。`status`: 任务执行状态。以`0`作为任务抓取的初始状态值，表示`UN_PROCESSED`，`1`表示PROCESSING,`2`表示PROCESSED

- `train_crawler.py`: 车次时刻表信息抓取爬虫。 

- `path_stations_crawler.py`:  经停靠站台信息抓取爬虫。

- `get_page.py `:  为防止反爬虫机制，由`requests`库改进而来的网页请求模块。这个模块中，集成了ip切换机制与其他强有力的反反爬虫技巧。

- `adsl_server.py`: ADSL拨号服务器运行的脚本。ADSL服务器与爬虫服务器，通过redis数据库进行通信。

  ​

#### 2. 使用方法：

- 配置`config.py`: 在`config.py`中添加对应的MongoDB地址和redis地址（在本项目中不是必须）。

- 在对应数据库中新建两个`collection`，在默认代码中两个`collection`位于`crawler_task_status`数据库下,分别是`train_info_test`和`path_stations_test`

- 数据存储方式，可以在`train_crawler.py（车次时刻表信息）`和`path_stations_crawler.py（某一车次停靠站详细信息）`

  ​