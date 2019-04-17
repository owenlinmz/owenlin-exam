# -*- coding: utf-8 -*-
"""Login middleware."""

from django.contrib.auth import authenticate
from django.middleware.csrf import get_token as get_csrf_token
from django.conf import settings

from account.accounts import Account
from conf.default import RUN_MODE


class LoginMiddleware(object):
    """Login middleware."""

    def process_view(self, request, view, args, kwargs):
        """process_view."""
        if RUN_MODE == "DEVELOP":
            request.user.username = "admin"
            request.user.is_superuser = True
            return None
        if getattr(view, 'login_exempt', False):
            return None

        # 对[公众号]weixin 路径不需要蓝鲸登录
        use_weixin = getattr(settings, "USE_WEIXIN", None)
        weixin_path_prefix = getattr(settings, "WEIXIN_SITE_URL", None)
        weixin_app_external_host = getattr(settings, "WEIXIN_APP_EXTERNAL_HOST", None)
        if (use_weixin and weixin_path_prefix and weixin_app_external_host and
                request.path.startswith(weixin_path_prefix) and request.get_host() == weixin_app_external_host):
            return None

        # 对于微信小程序的路径不需要蓝鲸登录
        use_miniweixin = getattr(settings, "USE_MINIWEIXIN", None)
        miniweixin_path_prefix = getattr(settings, "MINIWEIXIN_SITE_URL", None)
        miniweixin_app_external_host = getattr(settings, "MINIWEIXIN_APP_EXTERNAL_HOST", None)
        if (use_miniweixin and miniweixin_path_prefix and miniweixin_app_external_host and
                request.path.startswith(miniweixin_path_prefix) and request.get_host() == miniweixin_app_external_host):
            return None

        user = authenticate(request=request)
        if user:
            request.user = user
            get_csrf_token(request)
            return None

        account = Account()
        return account.redirect_login(request)
