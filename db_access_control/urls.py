from django.contrib import admin
from django.urls import path, include
from access_control.views import CustomLoginView
from two_factor.urls import urlpatterns as tf_urls
from django_otp.admin import OTPAdminSite
from access_control.admin import admin_site

admin.site.__class__ = OTPAdminSite
urlpatterns = [
    path('admin/login/', CustomLoginView.as_view(), name='custom_login'),
    path('admin/', admin_site.urls),  # admin.site.urls를 admin_site.urls로 변경
    path('access_control/', include('access_control.urls')),
    path('account/', include('django.contrib.auth.urls')),
    path('', include(tf_urls)),

    
]
