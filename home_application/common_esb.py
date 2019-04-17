# -*- coding: utf-8 -*-


def search_business_esb(client, username):
    """
    获取业务
    """
    params = {
        'bk_app_code': client.app_code,
        'bk_app_secret': client.app_secret,
        'bk_username': username,
        "fields": [
            "bk_biz_name", "bk_biz_id"
        ],
        "condition": {},
        "page": {
            "start": 0,
            "limit": 200
        }
    }
    res = client.cc.search_business(params)
    if res['result']:
        return {'data': res['data']['info']}
    return {'data': []}


def search_set_esb(client, username, bk_biz_id):
    """
    获取集群
    """
    params = {
        'bk_app_code': client.app_code,
        'bk_app_secret': client.app_secret,
        'bk_username': username,
        'bk_biz_id': bk_biz_id,
        "fields": [
            "bk_set_name", "bk_set_id"
        ],
        "condition": {},
        "page": {
            "start": 0,
            "limit": 200
        }
    }
    res = client.cc.search_set(params)
    if res['result']:
        return {'data': res['data']['info']}
    return {'data': []}


def search_host_esb(client, username, bk_biz_id=None):
    """
    通过业务ID或集群ID获取主机
    """

    params = {
        "bk_app_code": client.app_code,
        "bk_app_secret": client.app_secret,
        "bk_username": username,
        "condition": [
            {
                "bk_obj_id": "biz",
                "fields": [],
                "condition": []
            },
            {
                "bk_obj_id": "set",
                "fields": [],
                "condition": []
            },
            {
                "bk_obj_id": "module",
                "fields": [],
                "condition": []
            }
        ]
    }
    if bk_biz_id:
        params.update({
            'bk_biz_id': bk_biz_id
        })
    res = client.cc.search_host(params)
    if res['result']:
        return {'data': res['data']['info']}
    return {'data': []}


def execute_job_esb(client, username, data):
    params = {
        "bk_app_code": client.app_code,
        "bk_app_secret": client.app_secret,
        "bk_username": username
    }
    params.update(data)
    res = client.job.execute_job(params)
    if res['result']:
        return {'data': res['data']}
    return {'data': {}}


def fast_execute_script_esb(client, username, data, script_content):
    """
    快速执行脚本
    """
    params = {
        "bk_app_code": client.app_code,
        "bk_app_secret": client.app_secret,
        "bk_username": username,
        "script_content": script_content,
        "ip_list": data['ip_list'],
        "bk_biz_id": data['bk_biz_id'],
        "account": "root",
    }
    res = client.job.fast_execute_script(params)
    if res['result']:
        return {'data': res['data']}
    return {'data': {}}


def get_job_instance_log_esb(client, username, data):
    """
    查询作业执行日志
    """
    params = {
        "bk_app_code": client.app_code,
        "bk_app_secret": client.app_secret,
        "bk_username": username,
        "bk_biz_id": data['bk_biz_id'],
        "job_instance_id": data['job_instance_id']
    }
    res = client.job.get_job_instance_log(params)
    if res['result']:
        return {'data': res['data']}
    return {'data': []}


def fast_push_file_esb(client, biz_id, file_target_path, file_source, target_ip_list, file_source_ip_list,
                       username='admin'):
    """
    快速分发文件
    """
    params = {
        "bk_app_code": client.app_code,
        "bk_app_secret": client.app_secret,
        "bk_username": username,
        "bk_biz_id": int(biz_id),
        "file_target_path": file_target_path,
        "file_source": [
            {
                "files": file_source,
                "account": "root",
                "ip_list": file_source_ip_list,
                "custom_query_id": [
                    "3"
                ]
            }
        ],
        "ip_list": target_ip_list,
        "custom_query_id": [
            "3"
        ],
        "account": "root",
    }
    res = client.job.fast_push_file(params)
    return res
