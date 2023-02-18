from django.contrib import admin
from django.urls import path, include
import os



urlpatterns = [
    path('admin/', admin.site.urls),
]

DEBUG = os.environ.get('DEBUG')
if DEBUG == True:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]