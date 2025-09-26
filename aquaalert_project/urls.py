# aquaalert_project/urls.py

from django.contrib import admin
from django.urls import path, include # Make sure include is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # ADD THIS LINE
    path('', include('core.urls')),
]