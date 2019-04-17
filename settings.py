import os
from conf.default import *  # noqa
"""
You can load different configurations depending on yourcurrent environment.

 This can be the following values:

      development
      testing
      production
"""

ENVIRONMENT = os.environ.get("BK_ENV", "development")
# Inherit from environment specifics
conf_module = "conf.settings_%s" % ENVIRONMENT

try:
    module = __import__(conf_module, globals(), locals(), ['*'])
except ImportError, e:
    raise ImportError("Could not import conf '%s' (Is it on sys.path?): %s" % (conf_module, e))

for setting in dir(module):
    if setting == setting.upper():
        locals()[setting] = getattr(module, setting)


# check saas app  settings
try:
    saas_conf_module = "conf.settings_saas"
    saas_module = __import__(saas_conf_module, globals(), locals(), ['*'])
    for saas_setting in dir(saas_module):
        if saas_setting == saas_setting.upper():
            locals()[saas_setting] = getattr(saas_module, saas_setting)
except:
    pass


# check weixin settings
try:
    weixin_conf_module = "weixin.core.settings"
    weixin_module = __import__(weixin_conf_module, globals(), locals(), ['*'])
    for weixin_setting in dir(weixin_module):
        if weixin_setting == weixin_setting.upper():
            locals()[weixin_setting] = getattr(weixin_module, weixin_setting)
except:
    pass


# check mini weixin settings
try:
    miniweixin_conf_module = "miniweixin.core.settings"
    miniweixin_module = __import__(miniweixin_conf_module, globals(), locals(), ['*'])
    for miniweixin_setting in dir(miniweixin_module):
        if miniweixin_setting == miniweixin_setting.upper():
            locals()[miniweixin_setting] = getattr(miniweixin_module, miniweixin_setting)
except:
    pass
