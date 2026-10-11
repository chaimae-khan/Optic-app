# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # ← set_language endpoint
]

urlpatterns += i18n_patterns(
    path('', include('myapp.urls')),
    prefix_default_language=False,  # English stays at /, Arabic at /ar/, French at /fr/
)