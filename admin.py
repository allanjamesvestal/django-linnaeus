from operator import itemgetter

from django import http, template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import site
from django.contrib.contenttypes import views as contenttype_views
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache


from linnaeus.helpers import build_app_list, get_admin_type_description, get_admin_type_priority, get_verbose_admin_type

class LinnaeusAdmin(object):
    default_sidebar_template = None
#"admin/sidebar.html"
    front_page_sidebar_template = None
#"admin/sidebar.html"

    def __init__(self):
        admin.autodiscover()

    def get_urls(self):
#        admin.autodiscover()
        from django.conf.urls.defaults import patterns, url, include

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return site.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        # Admin-site-wide views.
        urls = patterns('',
            url(r'^$',
                wrap(self.front_page), 
                name='front_page'),
            url(r'^logout/$',
                wrap(site.logout),
                name='logout'),
            url(r'^password_change/$',
                wrap(site.password_change, cacheable=True),
                name='password_change'),
            url(r'^password_change/done/$',
                wrap(site.password_change_done, cacheable=True),
                name='password_change_done'),
            url(r'^jsi18n/$',
                wrap(site.i18n_javascript, cacheable=True),
                name='jsi18n'),
            url(r'^r/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                wrap(contenttype_views.shortcut)),
        )

        faceted_app_list = build_app_list(site._registry)

        for admin_type in faceted_app_list.keys():
            urls += patterns('',
                url(r'^%s/$' % admin_type,
                    wrap(self.index),
                    {'admin_type': admin_type,},
                    name='%s_index' % admin_type),
                url(r'^%s/(?P<app_label>\w+)/$' % admin_type,
                    wrap(self.app_index),
                    {'admin_type': admin_type,},
                    name='%s_app_index' % admin_type),
            )

            for model, model_admin in faceted_app_list[admin_type].iteritems():
                urls += patterns('',
                    url(r'^%s/%s/%s/' % (admin_type, model._meta.app_label, model._meta.module_name),
                        include(model_admin.urls)),
                )

        return urls

    @property
    def urls(self):
        return self.get_urls(), site.app_name, site.name

    @never_cache
    def front_page(self, request, extra_context=None, *args, **kwargs):
        """
        Displays the admin's front page, which lists all models in all
        installed apps, split up by which 'admin_type' (if any) they have
        been assigned in their respective ModelAdmin classes.
        """
        user = request.user

        apps = {}
        app_list = build_app_list(site._registry)

        for admin_type in app_list.keys():
            apps[admin_type] = {
                'apps': {},
                'description': get_admin_type_description(admin_type),
                'index_url': admin_type + '_index',
                'priority': get_admin_type_priority(admin_type),
                'raw_name': admin_type,
                'verbose_name': get_verbose_admin_type(admin_type),
            }

            for model, model_admin in app_list[admin_type].iteritems():
                app_label = model._meta.app_label
                has_module_perms = user.has_module_perms(app_label)

                if has_module_perms:
                    perms = model_admin.get_model_perms(request)
                    # Check whether user has any perm for this module.
                    # If so, add the module to the model_list.
                    if True in perms.values():
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'admin_url': mark_safe('%s/%s/%s/' % (admin_type, app_label, model.__name__.lower())),
                            'perms': perms,
                        }
                        if app_label in apps[admin_type]['apps']:
                            apps[admin_type]['apps'][app_label]['models'].append(model_dict)
                        else:
                            apps[admin_type]['apps'][app_label] = {
                                'name': app_label.title(),
                                'app_url': admin_type + '/' + app_label + '/',
                                'has_module_perms': has_module_perms,
                                'models': [model_dict],
                            }
            list = []
            for key in apps[admin_type]['apps'].keys():
                list.append(apps[admin_type]['apps'][key])
            apps[admin_type]['apps'] = list

        context = {
            'title': None,
            'app_list': sorted(apps.values(), key=itemgetter('priority', 'verbose_name')),
            'admin_front_page': True,
            'is_front_page': True,
            'sidebar_template': self.front_page_sidebar_template or self.default_sidebar_template or "admin/sidebar.html",
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=site.name)
        return render_to_response('admin/front_page.html', context,
            context_instance=context_instance
        )

    @never_cache
    def index(self, request, extra_context=None, *args, **kwargs):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """

        admin_type_filter = kwargs.pop('admin_type', None)
        if not admin_type_filter:
            try:
                admin_type_filter = settings.LINNAEUS_DEFAULT_ADMIN_TYPE
            except:
                admin_type_filter = 'default'

        app_dict = {}
        user = request.user
        faceted_app_list = build_app_list(site._registry)
        for model, model_admin in faceted_app_list[admin_type_filter].items():
            app_label = model._meta.app_label
            has_module_perms = user.has_module_perms(app_label)

            if has_module_perms:
                perms = model_admin.get_model_perms(request)

                # Check whether user has any perm for this module.
                # If so, add the module to the model_list.
                if True in perms.values():
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                        'perms': perms,
                    }
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': app_label.title(),
                            'app_url': app_label + '/',
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(key=lambda x: x['name'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        ## Retrieve the verbose admin type name and type descriptions, if they exist.
        admin_type_description = get_admin_type_description(admin_type_filter)
        admin_type_verbose = get_verbose_admin_type(admin_type_filter)

        context = {
            'title': _('%s administration') % capfirst(admin_type_verbose),
            'app_list': app_list,
            'root_path': site.root_path,
            'admin_type': admin_type_filter,
            'admin_type_description': admin_type_description,
            'admin_type_verbose': admin_type_verbose,
            'sidebar_template': self.default_sidebar_template or "admin/sidebar.html",
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=site.name)
        return render_to_response(site.index_template or 'admin/index.html', context,
            context_instance=context_instance
        )

    def app_index(self, request, app_label, extra_context=None, *args, **kwargs):
        user = request.user
        has_module_perms = user.has_module_perms(app_label)

        admin_type_filter = kwargs.pop('admin_type', None)
        if not admin_type_filter:
            try:
                admin_type_filter = settings.LINNAEUS_DEFAULT_ADMIN_TYPE
            except:
                admin_type_filter = 'default'

        app_dict = {}
        faceted_app_list = build_app_list(site._registry)
        for model, model_admin in faceted_app_list[admin_type_filter].items():
            if app_label == model._meta.app_label:
                if has_module_perms:
                    perms = model_admin.get_model_perms(request)

                    # Check whether user has any perm for this module.
                    # If so, add the module to the model_list.
                    if True in perms.values():
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'admin_url': '%s/' % model.__name__.lower(),
                            'perms': perms,
                        }
                        if app_dict:
                            app_dict['models'].append(model_dict),
                        else:
                            # First time around, now that we know there's
                            # something to display, add in the necessary meta
                            # information.
                            app_dict = {
                                'name': app_label.title(),
                                'app_url': '',
                                'has_module_perms': has_module_perms,
                                'models': [model_dict],
                            }

        ## Retrieve the verbose admin type name and type descriptions, if they exist.
        admin_type_description = get_admin_type_description(admin_type_filter)
        admin_type_verbose = get_verbose_admin_type(admin_type_filter)

        if not app_dict:
            raise http.Http404('The requested admin page does not exist.')
        # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])
        context = {
            'title': _('%s administration') % capfirst(app_label),
            'app_label': app_label,
            'app_list': [app_dict],
            'root_path': site.root_path,
            'admin_type': admin_type_filter,
            'admin_type_description': admin_type_description,
            'admin_type_verbose': admin_type_verbose,
            'sidebar_template': self.default_sidebar_template or "admin/sidebar.html",
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=site.name)
        return render_to_response(site.app_index_template or ('admin/%s/app_index.html' % app_label,
            'admin/app_index.html'), context,
            context_instance=context_instance
        )
