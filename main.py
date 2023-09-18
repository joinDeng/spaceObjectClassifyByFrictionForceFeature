# -*- coding = utf-8 -*-
# @Time:2023/9/12,16:34
# @Author:邓云龙
# @File:GP.py
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
    SpaceTrack描述轨道信息采用数据格式：TLE、3LE、OMM、GP_、GP_history
    随着编目增多，TLE越来越难以满足需求，18SDS未来将主要提供GP格式数据
    """

    # 编写日志。获取现在时间，记录下载数据时间点
    log_file_dir = "../getSpaceTargetTLE"
    if record_log:
        now_time = datetime.datetime.now()
        print(now_time)
        makeDir(log_file_dir)
        log_file = log_file_dir + '/' + 'log.txt'
        with open(log_file, 'a+') as log_f:
            log_f.write('update time: %s\n' % now_time)

    # 爬虫，获取所需数据
    cmd_login_zyl = 'curl.exe -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=zyl369ci@163.com&password=zhangyulu1997-DA'
    cmd_login_dyl = 'curl.exe -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=zyl369ci@163.com&password=Dyl0123456789!!'
    cmd_get_files = "curl.exe --cookie cookies.txt --limit-rate 100K https://www.space-track.org/basicspacedata/query/class/gp/"

    removeTxt(os.path.join(log_file_dir, 'cookies.txt'))  # 删除本地cookies.txt，更新cookie
    is_login_fail = os.system(cmd_login_zyl)  # 返回结果为0表示执行成功。
    print(f'login state: {not bool(is_login_fail)}')
    result_search = os.popen(cmd_get_files, 'r').read()  # os.popen返回的是一个file对象,os.popen()方法是非阻塞的。

    features = ["CCSDS_OMM_VERS", "COMMENT", "CREATION_DATE", "ORIGINATOR",
                "OBJECT_NAME", "OBJECT_ID",
                "CENTER_NAME", "REF_FRAME", "TIME_SYSTEM", "MEAN_ELEMENT_THEORY",
                "EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION",
                "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY",
                "EPHEMERIS_TYPE", "CLASSIFICATION_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO",
                "REV_AT_EPOCH", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT", "SEMIMAJOR_AXIS",
                "PERIOD", "APOAPSIS", "PERIAPSIS", "OBJECT_TYPE", "RCS_SIZE",
                "COUNTRY_CODE", "LAUNCH_DATE", "SITE", "DECAY_DATE", "FILE",
                "GP_ID", "TLE_LINE0", "TLE_LINE1", "TLE_LINE2"]

    # 提取GP数据
    pattern_file2GP = "{[\d\D]*?}"  # 提取GP的正则表达式。注：.:除\n之外的所有字符;?：调为非贪婪模式
    GP_sets = re.findall(pattern_file2GP, str(result_search))

    # 提取GP中各个特征
    list_pattern_GP2feature = []
    for feature in features:
        list_pattern_GP2feature.append( str('("' + f'{feature}' + '":){1}') + str('(\"[\d\D]*?\"|null){1}') )  # 获得特征的正则表达式

    # 空间目标GP数据保存路径
    save_dir = '../getSpaceTargetTLE/spaceTargets'
    makeDir(save_dir)

    gp = GP()
    for GP_ in GP_sets:
        strings_expect = []
        for i, feature in enumerate(features):
            string_find = re.findall(list_pattern_GP2feature[i], GP_)
            string_expect = string_find[0][1]
            if '"' in string_expect:
                gp[feature] = string_expect[1:-1]
            else:
                gp[feature] = string_expect
            strings_expect.append(gp[feature])
        # 写入对应xls表格
        save_file = save_dir + '/' + f'GP_ID:{gp["GP_ID"]}.xlsx'
        if os.path.exists(save_file):  # 存在，添加最新数据
            # 读取历史数据，比较CREATION_DATE
            data_frames = pd.read_excel(save_file)
            if data_frames[-1][2] == gp['CREATION_DATE']:  # 一致,不添加数据
                pass
            else:  # 不一致，添加数据
                with ExcelWriter(save_file, mode="a", engine="openpyxl") as writer:
                    df_to_write = pd.DataFrame(data=[strings_expect], columns=features)
                    df_to_write.to_excel(writer, sheet_name="Sheet3")

        else:  # 不存在，创建表格，并添加数据
            df_to_write_ = pd.DataFrame(data=[strings_expect], columns=features)
            df_to_write_.to_excel(save_file)  # 表格

