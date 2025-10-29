from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# https://drf-spectacular.readthedocs.io/en/latest/faq.html#my-swagger-ui-and-or-redoc-page-is-blank
#
# My Swagger UI and/or Redoc page is blank
#
# Chances are high that you are using django-csp.
# Take a look inside your browser console and confirm that you have Content Security Policy errors.
# By default, django-csp usually breaks our UIs for 2 reasons: external assets and inline scripts.

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(api_version='v1'), name='schema'),
    # Optional UI:
    path('doc/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
