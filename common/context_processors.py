# -*- coding: utf-8 -*-
"""
context_processor for common(setting)

除setting外的其他context_processor内容，均采用组件的方式(string)
"""
from django.conf import settings
import datetime


def mysetting(request):
    context = {
        # 基础信息
        'RUN_MODE': settings.RUN_MODE,
        'APP_ID': settings.APP_ID,
        'SITE_URL': settings.SITE_URL,
        # 静态资源
        'STATIC_URL': settings.STATIC_URL,
        'STATIC_VERSION': settings.STATIC_VERSION,
        # 登录跳转链接
        'LOGIN_URL': settings.LOGIN_URL,
        'LOGOUT_URL': settings.LOGOUT_URL,
        'BK_PAAS_HOST': '%s/app/list/' % settings.BK_PAAS_HOST,
        'BK_PLAT_HOST': settings.BK_PAAS_HOST,
        # 当前页面，主要为了login_required做跳转用
        'APP_PATH': request.get_full_path(),
        'NOW': datetime.datetime.now(),
    }
    # 对[公众号]weixin 路径不需要蓝鲸登录
    use_weixin = getattr(settings, "USE_WEIXIN", None)
    weixin_site_url = getattr(settings, "WEIXIN_SITE_URL", None)
    weixin_static_url = getattr(settings, "WEIXIN_STATIC_URL", None)
    if use_weixin and weixin_site_url and weixin_static_url:
        context.update({
            'WEIXIN_SITE_URL': weixin_site_url,
            'WEIXIN_STATIC_URL': weixin_static_url
        })

    return context
