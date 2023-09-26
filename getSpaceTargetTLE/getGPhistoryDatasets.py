# -*- coding = utf-8 -*-
# @Time:2023/9/26,16:24
# @Author:邓云龙
# @File:getGPhistoryDatasets.py
# @Software:PyCharm
import os
import re
import copy
import datetime
import numpy as np
import time
import pandas as pd
from pandas import ExcelWriter
from getSpaceTargetTLE import GP


def makeDir(file_dir):
    if os.path.exists(file_dir):
        print(file_dir + " has existed!")
    else:
        os.mkdir(file_dir)


def removeTxt(file_txt):
    if os.path.exists(file_txt):
        os.remove(file_txt)


record_log = True  # 记录日志信息


if __name__ == "__main__":
    """
    SpaceTrack描述轨道信息采用数据格式：TLE、3LE、OMM、GP
    随着编目增多，TLE越来越难以满足需求，18SDS未来将主要提供GP格式数据
    """

    GP_file_dir = "../getSpaceTargetTLE"
    makeDir(GP_file_dir)

    # 编写日志。获取现在时间，记录下载数据时间点
    if record_log:
        now_time = datetime.datetime.now()
        print(now_time)
        log_file = GP_file_dir + '/' + 'log.txt'
        with open(log_file, 'a+') as log_f:
            log_f.write('update time: %s\n' % now_time)

    # 爬虫，获取所需数据
    cmd_login_zyl = 'curl.exe -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=zyl369ci@163.com&password=zhangyulu1997-DA'
    cmd_login_dyl = 'curl.exe -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=zyl369ci@163.com&password=Dyl0123456789!!'

    removeTxt(os.path.join(GP_file_dir, 'cookies.txt'))  # 删除本地cookies.txt，更新cookie
    is_login_fail = os.system(cmd_login_zyl)  # 返回结果为0表示执行成功。
    print(f'login state: {not bool(is_login_fail)}')

    # 获取GP数据
    cmd_get_files_base = "curl.exe --cookie cookies.txt --limit-rate 100K https://www.space-track.org"
    request_controller = 'basicspacedata'
    request_action = 'query'
    predicate_value_pairs = 'class/gp_history'  # 查询GP_history
    query_epoch_begin, query_epoch_end = '1990-01-01', '2023-01-01'
    query_epoch_begin, query_epoch_end = '2022-01-01', '2023-01-01'
    file_format = 'json'

    max_norad_cat_id = 99999  # NORAD_CAT_ID编号。注意：80000--89999
    # 空间目标GP数据保存路径
    save_dir = '../getSpaceTargetTLE/spaceTargets'
    makeDir(save_dir)
    # 读取对象
    for norad_cat_id in range(10):  # norad_cat_id远少于gp_id，因此选择norad_cat_id
        predicate_value_pairs_PS = f'epoch/{query_epoch_begin}--{query_epoch_end}/norad_cat_id/{norad_cat_id}/format/{file_format}'
        cmd_get_files = cmd_get_files_base + '/' + request_controller + '/' + request_action + '/' + predicate_value_pairs + '/' + predicate_value_pairs_PS
        # 区分Norad_cat_id
        result_search = os.popen(cmd_get_files, 'r').read()  # os.popen返回的是一个file对象,os.popen()方法是非阻塞的。
        if result_search not in ['[]', [], '']:
            result_process = result_search.replace(',', ',\n')
            save_file = os.path.join(save_dir, str(f'NoradCatID_{norad_cat_id}.txt'))
            with open(save_file, 'a') as f:
                f.write(result_process)







