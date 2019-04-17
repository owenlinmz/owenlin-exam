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


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week='*'))
def get_load5():
    host_info_list = HostInfo.objects.filter(is_delete=False)
    ip_list = []
    if not host_info_list:
        return
    else:
        username = host_info_list[0].last_user
        bk_biz_id = host_info_list[0].bk_biz_id

    for host_info in host_info_list:
        ip_list.append({
            'ip': host_info.bk_host_innerip,
            'bk_cloud_id': host_info.bk_cloud_id
        })

    client = get_client_by_user(username)
    data = {
        'bk_biz_id': bk_biz_id,
        "bk_job_id": 1,
        "steps": [
            {
                "account": "root",
                "pause": 0,
                "is_param_sensitive": 0,
                "creator": "admin",
                "script_timeout": 1000,
                "last_modify_user": "admin",
                "block_order": 1,
                "name": "查看CPU负载",
                "script_content": "#!/bin/bash\n\ncat /proc/loadavg",
                "block_name": "查看CPU负载",
                "create_time": "2019-04-08 10:06:52 +0800",
                "last_modify_time": "2019-04-08 10:06:55 +0800",
                "ip_list": ip_list,
                "step_id": 1,
                "script_id": 2,
                "script_param": "",
                "type": 1,
                "order": 1,
                "script_type": 1
            }
        ]
    }
    res = execute_job_esb(client, username, data)
    time.sleep(5)
    if res['data']:
        params = {'bk_biz_id': data['bk_biz_id'], 'job_instance_id': res['data']['job_instance_id']}
        res = get_job_instance_log_esb(client, 'admin', params)

        for i in range(5):
            if res['data'][0]['status'] != 3:
                time.sleep(2)
                res = get_job_instance_log_esb(client, 'admin', params)
            else:
                break

        if res['data'][0]['status'] == 3:
            # 处理性能数据
            try:
                for result in res['data'][0]['step_results'][0]['ip_logs']:
                    load5 = result['log_content'].split(' ')[1]
                    ip = result['ip']
                    check_time = result['start_time'].split(' +')[0]
                    host_info = HostInfo.objects.get(bk_host_innerip=ip)
                    HostLoad5.objects.create(load5=load5,
                                             check_time=datetime.datetime.strptime(check_time, "%Y-%m-%d %H:%M:%S"),
                                             bk_host_innerip=host_info)
            except KeyError:
                logger.error(u"找不到负载数据")


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week='*'))
def get_mem():
    host_info_list = HostInfo.objects.filter(is_delete=False)
    ip_list = []
    if not host_info_list:
        return
    else:
        username = host_info_list[0].last_user
        bk_biz_id = host_info_list[0].bk_biz_id

    for host_info in host_info_list:
        ip_list.append({
            'ip': host_info.bk_host_innerip,
            'bk_cloud_id': host_info.bk_cloud_id
        })

    client = get_client_by_user(username)
    data = {
        'bk_biz_id': bk_biz_id,
        "bk_job_id": 1,
        "steps": [
            {
                "account": "root",
                "pause": 0,
                "is_param_sensitive": 0,
                "creator": "admin",
                "script_timeout": 1000,
                "last_modify_user": "admin",
                "block_order": 1,
                "name": "查看内存状态",
                "script_content": "#!/bin/bash\n\n# 查看内存状态\n\nfree -m",
                "block_name": "查看内存状态",
                "create_time": "2019-04-08 10:08:41 +0800",
                "last_modify_time": "2019-04-08 10:08:43 +0800",
                "ip_list": ip_list,
                "step_id": 1,
                "script_id": 4,
                "script_param": "",
                "type": 1,
                "order": 1,
                "script_type": 1
            }
        ]
    }
    res = execute_job_esb(client, username, data)
    time.sleep(5)
    if res['data']:
        params = {'bk_biz_id': data['bk_biz_id'], 'job_instance_id': res['data']['job_instance_id']}
        res = get_job_instance_log_esb(client, 'admin', params)

        for i in range(5):
            if res['data'][0]['status'] != 3:
                time.sleep(2)
                res = get_job_instance_log_esb(client, 'admin', params)
            else:
                break

        if res['data'][0]['status'] == 3:
            # 处理性能数据
            try:
                for result in res['data'][0]['step_results'][0]['ip_logs']:
                    mem = result['log_content'].split('\n')[1].split(' ')
                    real_mem = []
                    for item in mem:
                        if item:
                            real_mem.append(item)

                    ip = result['ip']
                    check_time = result['start_time'].split(' +')[0]
                    host_info = HostInfo.objects.get(bk_host_innerip=ip)
                    HostMem.objects.create(used_mem=real_mem[2],
                                           free_mem=real_mem[3],
                                           check_time=datetime.datetime.strptime(check_time, "%Y-%m-%d %H:%M:%S"),
                                           bk_host_innerip=host_info)
            except KeyError:
                logger.error(u"找不到内存数据")


@periodic_task(run_every=crontab(minute='*/1', hour='*', day_of_week='*'))
def get_disk():
    host_info_list = HostInfo.objects.filter(is_delete=False)
    ip_list = []
    if not host_info_list:
        return
    else:
        username = host_info_list[0].last_user
        bk_biz_id = host_info_list[0].bk_biz_id

    for host_info in host_info_list:
        ip_list.append({
            'ip': host_info.bk_host_innerip,
            'bk_cloud_id': host_info.bk_cloud_id
        })

    client = get_client_by_user(username)
    data = {
        'bk_biz_id': bk_biz_id,
        "bk_job_id": 1,
        "steps": [
            {
                "account": "root",
                "pause": 0,
                "is_param_sensitive": 0,
                "creator": "admin",
                "script_timeout": 1000,
                "last_modify_user": "admin",
                "block_order": 1,
                "name": "查看磁盘使用情况",
                "script_content": "#!/bin/bash\n\n# 查看磁盘使用情况\n\ndf -h",
                "block_name": "查看磁盘使用情况",
                "create_time": "2019-04-08 10:10:13 +0800",
                "last_modify_time": "2019-04-08 10:10:58 +0800",
                "ip_list": ip_list,
                "step_id": 1,
                "script_id": 7,
                "script_param": "",
                "type": 1,
                "order": 1,
                "script_type": 1
            }
        ]
    }
    res = execute_job_esb(client, username, data)
    time.sleep(5)
    if res['data']:
        params = {'bk_biz_id': data['bk_biz_id'], 'job_instance_id': res['data']['job_instance_id']}
        res = get_job_instance_log_esb(client, 'admin', params)

        for i in range(5):
            if res['data'][0]['status'] != 3:
                time.sleep(2)
                res = get_job_instance_log_esb(client, 'admin', params)
            else:
                break

        if res['data'][0]['status'] == 3:
            # 处理性能数据
            try:
                for result in res['data'][0]['step_results'][0]['ip_logs']:
                    disk = result['log_content'].split('\n')
                    ip = result['ip']
                    check_time = result['start_time'].split(' +')[0]
                    host_info = HostInfo.objects.get(bk_host_innerip=ip)
                    HostDisk.objects.create(disk=json.dumps(disk),
                                            check_time=datetime.datetime.strptime(check_time, "%Y-%m-%d %H:%M:%S"),
                                            bk_host_innerip=host_info)
            except KeyError:
                logger.error(u"找不到磁盘数据")
