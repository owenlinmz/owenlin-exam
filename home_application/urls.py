# -*- coding: utf-8 -*-

from django.conf.urls import patterns

urlpatterns = patterns(
    'home_application.views',
    (r'^$', 'home'),
    (r'^dev-guide/$', 'dev_guide'),
    (r'^contactus/$', 'contactus'),
    (r'^api/test/$', 'test'),
    (r'^performance/$', 'performance'),

    (r'^get_set/$', 'get_set'),
    (r'^get_biz/$', 'get_biz'),
    (r'^search_host/$', 'get_host'),
    (r'^get_new_pfm/$', 'get_new_pfm'),
    (r'^switch_pfm/$', 'switch_pfm'),
    (r'^list_host/$', 'list_host'),

    (r'^display_performance/$', 'display_performance'),
    (r'^display_performance_new/$', 'display_performance_new'),

)
