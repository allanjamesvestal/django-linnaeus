from django.conf import settings
from django.contrib import admin
from django.db import models

def admin_type_for_app_and_model(app_label, module_name):
    model = models.get_model(app_label, module_name)
    admin_type = admin_type_for_model(model)
    return admin_type

def admin_type_for_model(model):
    admin.autodiscover()
    model_admin = admin.site._registry[model]

    admin_type = admin_type_lookup(model_admin)
    return admin_type

def admin_type_for_object(object):
    admin_type = admin_type_for_model(object.__class__)
    return admin_type

def admin_type_lookup(model_admin):
    if hasattr(model_admin, 'admin_type'):
        return model_admin.admin_type
    else:
        try:
            return settings.LINNAEUS_DEFAULT_ADMIN_TYPE
        except:
            return 'default'

def build_app_list(site_registry):
    """
    Constructs a dictionary of apps based on the "admin_type" settings
    in each app's admin configuration.

    Takes one argument, the site._registry item of the current admin site.
    """
    try:
        default_type = settings.DEFAULT_ADMIN_TYPE
    except:
        default_type = 'default'

    site_dict = {}

    for model, model_admin in site_registry.iteritems():
        model_admin_type = admin_type_lookup(model_admin)

        if model_admin_type in site_dict.keys():
            site_dict[model_admin_type][model] = model_admin
        else:
            site_dict[model_admin_type] = {model: model_admin}

    return site_dict

def get_admin_type_description(admin_type_raw):
    from linnaeus.config import build_config_list, linnaeus
    build_config_list()
    return linnaeus._registry[admin_type_raw].description    

def get_admin_type_priority(admin_type_raw):
    from linnaeus.config import build_config_list, linnaeus
    build_config_list()
    return linnaeus._registry[admin_type_raw].display_priority

def get_admin_type_template(admin_type_raw, template_type="index"):
    from linnaeus.config import build_config_list, linnaeus
    build_config_list()
    if template_type == "index":
        return linnaeus._registry[admin_type_raw].type_sidebar_template
    elif template_type == "app_index":
        return linnaeus._registry[admin_type_raw].type_app_sidebar_template
    return ''

def get_verbose_admin_type(admin_type_raw):
    from linnaeus.config import build_config_list, linnaeus
    build_config_list()
    return linnaeus._registry[admin_type_raw].get_verbose_name()
