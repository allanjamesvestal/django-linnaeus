from django import template
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType

from linnaeus.helpers import build_app_list

register = template.Library()

class AdminLogNode(template.Node):
    def __init__(self, admin_type, limit, varname, user):
        self.admin_type, self.limit, self.varname, self.user = admin_type, limit, varname, user

    def __repr__(self):
        return "<GetAdminLog Node>"

    def render(self, context):
        admin_type = context[self.admin_type]

        admin.autodiscover()
        app_list = build_app_list(admin.site._registry)

        type_apps = app_list[admin_type].keys()

        type_cts = []
        for app in type_apps:
            type_cts.append(ContentType.objects.get(app_label=app._meta.app_label, model=app._meta.module_name))

        if self.user is None:
            context[self.varname] = LogEntry.objects.filter(content_type__in=type_cts).select_related('content_type', 'user')[:self.limit]
        else:
            user_id = self.user
            if not user_id.isdigit():
                user_id = context[self.user].id
            context[self.varname] = LogEntry.objects.filter(content_type__in=type_cts, user__id__exact=user_id).select_related('content_type', 'user')[:self.limit]
        return ''

@register.tag
def get_admin_log_for_type(parser, token):
    """
    Populates a template variable with the admin log for the given criteria.

    Usage::

        {% get_admin_log_for_type [admin_type] [limit] as [varname] for_user [context_var_containing_user_obj] %}

    Examples::

        {% get_admin_log_for_type sample 10 as admin_log for_user 23 %}
        {% get_admin_log_for_type sample 10 as admin_log for_user user %}
        {% get_admin_log_for_type sample 10 as admin_log %}

    Note that ``context_var_containing_user_obj`` can be a hard-coded integer
    (user ID) or the name of a template context variable containing the user
    object whose ID you want.
    """
    tokens = token.contents.split()
    if len(tokens) < 5:
        raise template.TemplateSyntaxError(
            "'get_admin_log' statements require three arguments")
    if not tokens[2].isdigit():
        raise template.TemplateSyntaxError(
            "Second argument to 'get_admin_log' must be an integer")
    if tokens[3] != 'as':
        raise template.TemplateSyntaxError(
            "Third argument to 'get_admin_log' must be 'as'")
    if len(tokens) > 5:
        if tokens[5] != 'for_user':
            raise template.TemplateSyntaxError(
                "Fifth argument to 'get_admin_log' must be 'for_user'")
    return AdminLogNode(admin_type=tokens[1], limit=tokens[2], varname=tokens[4], user=(len(tokens) > 5 and tokens[6] or None))
