from django.conf import settings
from django.contrib import admin
from django.utils.encoding import smart_str
from django.utils.importlib import import_module

from linnaeus.admin import LinnaeusAdmin
from linnaeus.helpers import build_app_list

class SiteConfig(object):
    def __init__(self):
        self._registry = {}

    def register(self, admin_type, admin_type_config):
        self._registry[admin_type] = admin_type_config(admin_type)

class TypeConfig(object):
    description = None
    display_priority = 1
    type_sidebar_template = None
    type_app_sidebar_template = None
    verbose_name = None

    def __init__(self, type):
        self.type = type.lower()
        if self.type_sidebar_template and not self.type_app_sidebar_template:
            self.type_app_sidebar_template = self.type_sidebar_template

    def __repr__(self):
        return smart_str(u"<%s: Configuration for '%s' admin type>" % (self.__class__.__name__, self.type))

    def get_verbose_name(self):
        if self.verbose_name:
            return self.verbose_name.lower()
        return self.type

def build_config_list():
    admin.autodiscover()
    app_list = build_app_list(admin.site._registry)
    admin_types = app_list.keys()

    custom_config = getattr(settings, 'LINNAEUS_SITECONF', None)

    if 'linnaeus' in settings.INSTALLED_APPS and custom_config:
        import_module(custom_config)

    for key in admin_types:
        if key in linnaeus._registry.keys():
            pass
        else:
            linnaeus.register(key, TypeConfig)
#            config = TypeConfig(key)
#            configs[key] = config

def register_type_config(admin_type, admin_type_config):
    type = admin_type_config(admin_type)
    return type

linnaeus = SiteConfig()
