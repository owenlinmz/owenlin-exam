# -*- coding: utf-8 -*-
"""
celery 任务示例

本地启动celery命令: python  manage.py  celery  worker  --settings=settings
周期性任务还需要启动celery调度命令：python  manage.py  celerybeat --settings=settings
"""
import base64
import datetime
import json
import time

import requests
from celery import task
from celery.schedules import crontab
from celery.task import periodic_task
from django.http import JsonResponse

from blueking.component.shortcuts import get_client_by_user
from common.log import logger
from home_application.common_esb import fast_execute_script_esb, get_job_instance_log_esb, execute_job_esb
# from home_application.models import HostInfo, HostLoad5, HostMem, HostDisk
from home_application.models import HostInfo, HostPerformance


@task()
def async_task(x, y):
    """
    定义一个 celery 异步任务
    """
    # logger.error(u"celery 定时任务执行成功，执行结果：{:0>2}:{:0>2}".format(x, y))
    # return x + y
    pass


def execute_task():
    """
    执行 celery 异步任务

    调用celery任务方法:
        task.delay(arg1, arg2, kwarg1='x', kwarg2='y')
        task.apply_async(args=[arg1, arg2], kwargs={'kwarg1': 'x', 'kwarg2': 'y'})
        delay(): 简便方法，类似调用普通函数
        apply_async(): 设置celery的额外执行选项时必须使用该方法，如定时（eta）等
                      详见 ：http://celery.readthedocs.org/en/latest/userguide/calling.html
    """
    # now = datetime.datetime.now()
    # logger.error(u"celery 定时任务启动，将在60s后执行，当前时间：{}".format(now))
    # # 调用定时任务
    # async_task.apply_async(args=[now.hour, now.minute], eta=now + datetime.timedelta(seconds=60))
    pass


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week='*'))
def get_pfm():
    start = datetime.datetime.now()
    # logger.info(u"开始获取...{}".format(start))
    host_info_list = HostInfo.objects.filter(is_delete=False, bk_os_name__contains='linux')
    ip_list = []
    for host_info in host_info_list:
        ip_list.append({
            'ip': host_info.bk_host_innerip,
            'bk_cloud_id': host_info.bk_cloud_id
        })
    if host_info_list:
        username = host_info_list[0].last_user
        bk_biz_id = host_info_list[0].bk_biz_id
        client = get_client_by_user(username)
        script_content = '''#!/bin/bash
MEMORY=$(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }')
DISK=$(df -h | awk '$NF=="/"{printf "%s", $5}')
CPU=$(top -bn1 | grep load | awk '{printf "%.2f%%", $(NF-2)}')
DATE=$(date "+%Y-%m-%d %H:%M:%S")
echo -e "$DATE|$MEMORY|$DISK|$CPU"
            '''
        data = {
            'ip_list': ip_list,
            'bk_biz_id': bk_biz_id
        }
        res = fast_execute_script_esb(client, username, data, base64.b64encode(script_content))
        time.sleep(5)
        if res['data']:
            params = {}
            params.update({'bk_biz_id': data['bk_biz_id'], 'job_instance_id': res['data']['job_instance_id']})
            res = get_job_instance_log_esb(client, username, params)

            for i in range(5):
                if res['data'][0]['status'] != 3:
                    time.sleep(2)
                    res = get_job_instance_log_esb(client, username, params)
                else:
                    break

            if res['data'][0]['status'] == 3:
                # 处理性能数据
                try:
                    pfm_data = res['data'][0]['step_results'][0]['ip_logs']
                except KeyError:
                    pfm_data = []
                for item in pfm_data:
                    result = item['log_content'].split('|')
                    check_time = result[0]
                    mem = result[1]
                    disk = result[2]
                    cpu = result[3]
                    ip = item['ip']
                    host_info = HostInfo.objects.get(bk_host_innerip=ip)
                    host_pfm = HostPerformance.objects.create(
                        bk_host_innerip=host_info,
                        check_time=datetime.datetime.strptime(check_time, "%Y-%m-%d %H:%M:%S"),
                        mem=mem,
                        disk=disk,
                        cpu=cpu
                    )
                    # now = datetime.datetime.now()
                    # logger.info(u"主机{}完成一条性能查询：{}".format(host_pfm.bk_host_innerip, now))
