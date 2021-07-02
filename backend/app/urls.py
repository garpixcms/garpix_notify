from django.contrib import admin
from django.urls import path, include
from .views import example_send_notify

urlpatterns = [
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('', example_send_notify),
]
