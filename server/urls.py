"""
Main URL mapping configuration file.

Include other URLConfs from external apps using method `include()`.

It is also a good practice to keep a single URL to the root index page.

This examples uses Django's default media
files serving technique in development.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.admindocs import urls as admindocs_urls
from django.urls import include, path
from django.views.generic import TemplateView
from health_check import urls as health_urls

from server.apps.main import urls as main_urls
from server.apps.authentication import urls as auth_urls
from server.apps.openapi import urls as openapi_urls
from server.apps.main.views import index
from server.settings.components import config

admin.autodiscover()

urlpatterns = [
    # Apps:
    path('main/', include(main_urls, namespace='main')),
    # Health checks:
    path('health/', include(health_urls)),
    # django-admin:
    path('admin/doc/', include(admindocs_urls)),
    path('admin/', admin.site.urls),
    path('api/', include(auth_urls)),
    path('api/', include(openapi_urls)),
    # Text and xml static files:
    path(
        'robots.txt',
        TemplateView.as_view(
            template_name='common/txt/robots.txt',
            content_type='text/plain',
        ),
    ),
    path(
        'humans.txt',
        TemplateView.as_view(
            template_name='common/txt/humans.txt',
            content_type='text/plain',
        ),
    ),
    # It is a good practice to have explicit index view:
    path('', index, name='index'),
]

# Документация Sphinx - только в development режиме
if config('DJANGO_ENV') == 'development':
    import debug_toolbar  # noqa: WPS433
    urlpatterns += [
        path('sphinx/', include('docs.urls')),
    ]

    urlpatterns = [
        # URLs specific only to django-debug-toolbar:
        path('__debug__/', include(debug_toolbar.urls)),
        *urlpatterns,
    ]
