from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from linnaeus import admin

class CustomAdmin(admin.LinnaeusAdmin):
    default_sidebar_template = 'nando/sidebar.html'    
linnaeus = CustomAdmin()

urlpatterns = patterns('',
    url(r'', include(linnaeus.urls)),
#    (r'^grappelli/', include('grappelli.urls')),
)

urlpatterns += patterns('',
    url(r'^_/lookup/related/$',
        'linnaeus.views.related.related_lookup',
        name='related_lookup'),
    url(r'^_/lookup/m2m/$',
        'linnaeus.views.related.m2m_lookup',
        name='m2m_lookup'),
    url(r'^_/lookup/autocomplete/$',
        'linnaeus.views.related.autocomplete_lookup',
        name='autocomplete_lookup'),
    (r'^comments/', include('django.contrib.comments.urls')),
)

urlpatterns += staticfiles_urlpatterns()
