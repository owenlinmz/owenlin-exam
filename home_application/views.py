# -*- coding: utf-8 -*-
import base64
import datetime
import json
import time

import requests
from django.forms import model_to_dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from account.decorators import login_exempt
from blueking.component.shortcuts import get_client_by_user, get_client_by_request
from common.log import logger
from common.mymako import render_mako_context
from common.mymako import render_json
from conf.default import APP_ID, APP_TOKEN, BK_PAAS_HOST

from home_application.common_esb import get_job_instance_log_esb, fast_execute_script_esb, search_host_esb, \
    search_set_esb, search_business_esb, fast_push_file_esb, execute_job_esb
from home_application.models import HostInfo, HostPerformance


def home(request):
    """
    首页
    """
    return render_mako_context(request, '/home_application/home.html')


def dev_guide(request):
    """
    开发指引
    """
    return render_mako_context(request, '/home_application/dev_guide.html')


def contactus(request):
    """
    联系我们
    """
    return render_mako_context(request, '/home_application/contact.html')


def performance(request):
    """
    测试
    """
    return render_mako_context(request, '/home_application/performance.html')


def test(request):
    return render_json({"result": 'ok', "username": request.user.username})


@csrf_exempt
def get_biz(request):
    client = get_client_by_request(request)
    res = search_business_esb(client, request.user.username)
    return render_json(res)


@csrf_exempt
def get_set(request):
    bk_biz_id = request.GET.get('bk_biz_id')
    client = get_client_by_request(request)
    res = search_set_esb(client, request.user.username, bk_biz_id)
    return render_json(res)


@csrf_exempt
def get_host(request):
    params = json.loads(request.body)
    bk_host_innerip__in = params.get('bk_host_innerip__in')
    client = get_client_by_request(request)
    res = search_host_esb(client, request.user.username)
    result = []
    for item in res['data']:
        params = {
            'bk_host_innerip': item['host']['bk_host_innerip'],
            'bk_host_name': item['host']['bk_host_name'],
            'bk_os_name': item['host']['bk_os_name'],
            'bk_inst_name': item['host']['bk_cloud_id'][0]['bk_inst_name'],
            'bk_cloud_id': item['host']['bk_cloud_id'][0]['id'],
            'bk_biz_id': item['biz'][0]['bk_biz_id'],
            'bk_biz_name': item['biz'][0]['bk_biz_name'],
            'last_user': request.user.username
        }
        host_info, is_exist = HostInfo.objects.update_or_create(**params)
        if is_exist:
            host_info.last_user = request.user.username
            host_info.save()

    if bk_host_innerip__in:
        bk_host_innerip__in = bk_host_innerip__in.split(',')
        host_info = HostInfo.objects.filter(bk_host_innerip__in=bk_host_innerip__in)
    else:
        host_info = HostInfo.objects.all()
    for host in host_info:
        result.append(model_to_dict(host))

    return render_json({'data': result})


@csrf_exempt
def get_new_pfm(request):
    ip = request.GET.get('ip')
    host_info = HostInfo.objects.get(bk_host_innerip=ip)
    host_performance = HostPerformance.objects.filter(bk_host_innerip=host_info, is_delete=False).order_by(
        'check_time').last()
    if host_performance:
        host_info.disk = host_performance.disk
        host_info.mem = host_performance.mem
        host_info.cpu = host_performance.cpu
        host_info.save()
    return render_json({'data': model_to_dict(host_info)})


@csrf_exempt
def list_host(request):
    host_list = HostInfo.objects.filter(is_delete=False)
    result = []
    for host in host_list:
        result.append(host.bk_host_innerip)
    return render_json({'data': result})


@csrf_exempt
def switch_pfm(request):
    params = json.loads(request.body)
    host_info = HostInfo.objects.get(bk_host_innerip=params['ip'])
    host_info.is_delete = params['is_delete']
    if host_info.is_delete:
        host_info.cpu = '--'
        host_info.mem = '--'
        host_info.disk = '--'
    host_info.save()
    return render_json({'data': model_to_dict(host_info)})


@csrf_exempt
def display_performance(request):
    """
    用于展示性能图表
    """

    # 处理单个主机的性能数据
    def generate_data(pfm_list):
        if not pfm_list:
            return {
                "xAxis": [],
                "series": [],
                "title": u"无数据"
            }
        xAxis = []
        series = []
        mem = []
        cpu = []
        disk = []
        for host_pfm in pfm_list:
            xAxis.append(host_pfm.check_time.strftime("%Y-%m-%d %H:%M:%S"))
            mem.append(float(host_pfm.mem.strip('%')))
            cpu.append(float(host_pfm.cpu.strip('%\n')))
            disk.append(float(host_pfm.disk.strip('%')))
        series.append({
            'name': 'mem',
            'type': 'line',
            'data': mem
        })
        series.append({
            'name': 'cpu',
            'type': 'line',
            'data': cpu
        })
        series.append({
            'name': 'disk',
            'type': 'line',
            'data': disk
        })
        return {
            "xAxis": xAxis,
            "series": series,
            "title": pfm_list[0].bk_host_innerip.bk_host_innerip
        }

    params = json.loads(request.body)
    result = []
    params.update({
        'bk_host_innerip_id': HostInfo.objects.get(bk_host_innerip=params.pop('ip')).id
    })

    host_pfm_list = HostPerformance.objects.filter(**params).order_by('-check_time')[:60].reverse()
    result.append(generate_data(host_pfm_list))
    return render_json({'data': result})


@csrf_exempt
def display_performance_new(request):
    params = json.loads(request.body)
    params.update({
        'bk_host_innerip_id': HostInfo.objects.get(bk_host_innerip=params.pop('ip')).id
    })

    host_pfm_list = HostPerformance.objects.filter(**params).order_by('-check_time')[:60].reverse()
    data = []
    for pfm in host_pfm_list:
        data.append({
            "time": pfm.check_time.strftime("%Y-%m-%d %H:%M:%S"),
            "mem": float(pfm.mem.strip('%')),
            "disk": float(pfm.disk.strip('%')),
            "cpu": float(pfm.cpu.strip('%\n'))
        })
    return render_json({'data': data})


class CommonUtil(object):

    @classmethod
    def pop_useless_params(self, params):
        # 请求参数处理
        pop_keys = []
        for key, value in params.items():
            if value == '':
                pop_keys.append(key)
            if key.endswith('__in'):
                params[key] = str(value).split(',')
        for pop in pop_keys:
            params.pop(pop)
        return params

    @classmethod
    def time_to_str(cls, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def str_to_time(cls, st):
        return datetime.datetime.strptime(st, "%Y-%m-%d %H:%M:%S")


def fast_push_file(request):
    client = get_client_by_request(request)
    biz_id = request.GET.get('biz_id')
    file_target_path = "/tmp/"
    target_ip_list = [{
        "bk_cloud_id": 0,
        "ip": "192.168.240.52"
    },
        {
            "bk_cloud_id": 0,
            "ip": "192.168.240.55"
        }
    ]
    file_source_ip_list = [{
        "bk_cloud_id": 0,
        "ip": "192.168.240.43"
    }
    ]
    file_source = ["/tmp/test12.txt"]
    data = fast_push_file_esb(client, biz_id, file_target_path, file_source, target_ip_list, file_source_ip_list,
                              request.user.username)
    return JsonResponse(data)
