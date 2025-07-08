from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include your app's URLs
]

if settings.DEBUG:
    handler404 = 'core.views.error_view'
    