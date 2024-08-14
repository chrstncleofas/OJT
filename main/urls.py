from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('students.urls')),
    path('adminSite/', include('app.urls')),
    path('admin/', admin.site.urls),
]
