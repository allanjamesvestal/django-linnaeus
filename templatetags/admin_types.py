from operator import itemgetter

from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.formats import get_format
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from linnaeus.admin import LinnaeusAdmin
from linnaeus.helpers import admin_type_for_app_and_model, admin_type_for_model, admin_type_for_object, build_app_list, get_admin_type_priority, get_admin_type_template, get_verbose_admin_type

register = template.Library()

@register.tag
def admin_type_from_object(parser, token):
    try:
        tag_name, obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]
    return TypeForObject(obj)

class TypeForObject(template.Node):
    def __init__(self, obj):
        self.object = template.Variable(obj)

    def render(self, context):
        obj = self.object.resolve(context)

        context['admin_type'] = admin_type_for_object(obj)
        context['admin_type_verbose'] = capfirst(get_verbose_admin_type(admin_type_for_object(obj)))
        return ''

@register.tag
def admin_type_from_meta(parser, token):
    try:
        tag_name, opts = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]
    return TypeForMeta(opts)

class TypeForMeta(template.Node):

    def __init__(self, opts):
        self.meta_class = template.Variable(opts)

    def render(self, context):
        meta_class = self.meta_class.resolve(context)

        context['admin_type'] = admin_type_for_app_and_model(meta_class.app_label, meta_class.module_name)
        context['admin_type_verbose'] = capfirst(get_verbose_admin_type(admin_type_for_app_and_model(meta_class.app_label, meta_class.module_name)))
        return ''

@register.simple_tag()
def get_admin_title():
    """
    Returns the title for the admin panel.
    """
    admin_title = getattr(settings, "LINNAEUS_ADMIN_TITLE", 'Linnaeus')
    return admin_title

@register.inclusion_tag('admin/render_sidebar.html', takes_context=True)
def render_sidebar(context):
    user = context['user']

    default_sidebar_template = context['sidebar_template']

    try:
        is_front = context['is_front_page']
    except:
        is_front = False

    if is_front:
        admin_type = None
        admin_type_verbose = None
        app_label = None
        template = default_sidebar_template
    else:
        try:
            app_label = context['app_label']
        except:
            app_label = None

        admin_type = context['admin_type']
        admin_type_verbose = context['admin_type_verbose']

        if app_label:
            template = get_admin_type_template(admin_type, "app_index")
        else:
            template = get_admin_type_template(admin_type, "index")

        if not template:
            template = default_sidebar_template

    return {
        'admin_type': admin_type,
        'admin_type_verbose': admin_type_verbose,
        'app_label': app_label,
        'template': template,
        'user': user,
    }

@register.inclusion_tag('admin/topbar_nav.html', takes_context=True)
def render_topbar_nav(context):
    admin.autodiscover()
    admin_type_list = build_app_list(admin.site._registry).keys()
    admin_type_list.sort()

    all_admin_types = []
    for type in admin_type_list:
        all_admin_types.append({
            'admin_type': type,
            'admin_type_priority': get_admin_type_priority(type),
            'admin_type_verbose': get_verbose_admin_type(type),
        })

    try:
        admin_type = context['admin_type']
    except:
        admin_type = None

    try:
        is_front_page = context['admin_front_page']
    except:
        is_front_page = False

    more_menu_active = False
    app_counter = 0

    all_admin_types = sorted(all_admin_types, key=itemgetter('admin_type_priority', 'admin_type_verbose'))

    if len(all_admin_types) > 4:
        if admin_type:
            for type in all_admin_types:
                app_counter += 1
                if type['admin_type'] == admin_type:
                    if app_counter > 4:
                        more_menu_active = True

    return {
        'admin_type': admin_type,
        'all_admin_types': all_admin_types,
        'is_front_page': is_front_page,
        'more_active': more_menu_active,
    }

@register.simple_tag()
def get_date_format():
    return get_format('DATE_INPUT_FORMATS')[0]

@register.simple_tag()
def get_time_format():
    return get_format('TIME_INPUT_FORMATS')[0]

@register.simple_tag()
def get_datetime_format():
    return get_format('DATETIME_INPUT_FORMATS')[0]

# All filters & tags below this point adapted from django-grappelli
# (http://github.com/sehmaschine/django-grappelli/). Thanks to its authors.

# GENERIC OBJECTS

class do_get_generic_objects(template.Node):
    
    def __init__(self):
        pass
    
    def render(self, context):
        return_string = "{"
        for c in ContentType.objects.all().order_by('id'):
            return_string = "%s%s: {pk: %s, app: '%s', model: '%s'}," % (return_string, c.id, c.id, c.app_label, c.model)
        return_string = "%s}" % return_string[:-1]
        return return_string

@register.tag()
def get_content_types(parser, token):
    """
    Returns a list of installed applications and models.
    Needed for lookup of generic relationships.
    """
    tokens = token.contents.split()
    return do_get_generic_objects()

# FORMSETSORT FOR SORTABLE INLINES

@register.filter
def formsetsort(formset, arg):
    """
    Takes a list of formset dicts, returns that list sorted by the sortable field.
    """
    
    if arg:
        sorted_list = []
        for item in formset:
            position = item.form[arg].data
            if position and position != "-1":
                sorted_list.append((int(position), item))
        sorted_list.sort()
        sorted_list = [item[1] for item in sorted_list]
        for item in formset:
            position = item.form[arg].data
            if not position or position == "-1":
                sorted_list.append(item)
    else:
        sorted_list = formset
    return sorted_list

# RELATED LOOKUPS

@register.simple_tag()
def get_related_lookup_fields_fk(model_admin):
    try:
        value = model_admin.related_lookup_fields.get("fk", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value

@register.simple_tag()
def get_related_lookup_fields_m2m(model_admin):
    try:
        value = model_admin.related_lookup_fields.get("m2m", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value

@register.simple_tag()
def get_related_lookup_fields_generic(model_admin):
    try:
        value = model_admin.related_lookup_fields.get("generic", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value

# AUTOCOMPLETES

@register.simple_tag()
def get_autocomplete_lookup_fields_fk(model_admin):
    try:
        value = model_admin.autocomplete_lookup_fields.get("fk", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value

@register.simple_tag()
def get_autocomplete_lookup_fields_m2m(model_admin):
    try:
        value = model_admin.autocomplete_lookup_fields.get("m2m", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value

@register.simple_tag()
def get_autocomplete_lookup_fields_generic(model_admin):
    try:
        value = model_admin.autocomplete_lookup_fields.get("generic", [])
        value = mark_safe(list(value))
    except:
        value = []
    return value
