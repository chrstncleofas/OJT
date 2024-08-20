from superapp import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'superapp'

urlpatterns = [
    path('', views.superHome, name='superHome'),
    path('editUserProfile/', views.editUserProfile, name='editUserProfile'),
    path('editUsers/<int:id>/', views.editUsers, name='editUsers'),
    path('createUserAdmin', views.createUserAdmin, name='createUserAdmin'),
    path('superLogin', views.superAdminLogin, name='superLogin'),
    path('addUsers', views.addUsers, name='addUsers'),
    path('loggingOut/', views.loggingOut, name='loggingOut'),
    path('superAdminDashboard/', views.superAdminDashboard, name='superAdminDashboard'),
    path('mainDashboard/', views.mainDashboard, name='mainDashboard'),
    path('getAllTheUserAccount/', views.getAllTheUserAccount, name='getAllTheUserAccount'),
    path('getActivityLogs/', views.getActivityLogs, name='getActivityLogs'),
    path('studentManagement/', views.studentManagement, name='studentManagement'),
    path('set_rendering_hours/', views.set_rendering_hours, name='set_rendering_hours'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
