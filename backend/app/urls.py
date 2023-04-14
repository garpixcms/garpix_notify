from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from .views import example_send_notify

urlpatterns = [
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('admin/', admin.site.urls),
    path('', example_send_notify),
    path('', include(('garpix_notify.urls', 'garpix_notify'), namespace='garpix_notify')),
]

if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
