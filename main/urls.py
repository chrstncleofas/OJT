from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('students.urls')),
    path('admin/', admin.site.urls),
    path('adminSite/', include('app.urls')),
    path('super-admin-page/', include('superapp.urls')),
]
