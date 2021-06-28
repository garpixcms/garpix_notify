from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.i18n import i18n_patterns
from django.http import Http404
from django.conf import settings
from .views import example_send_notify

urlpatterns = [
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('', example_send_notify),
    # re_path(r'page_api/(?P<slugs>.*)$', PageApiView.as_view()),
]

