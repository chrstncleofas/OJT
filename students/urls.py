from students import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'students'

urlpatterns = [
    path('', views.studentHome, name='home'),
    path('login', views.studentLogin, name='login'),
    path('register/', views.studentRegister, name='register'),
    path('dashboard/', views.studentDashboard, name='dashboard'),
    path('studentPage/', views.welcomeDashboard, name='studentPage'),
    path('Dashboard/', views.mainPageForDashboard, name='Dashboard'),
    path('TimeInAndTimeOut/', views.TimeInAndTimeOut, name='TimeInAndTimeOut'),
    path('capture-image/', views.capture_image, name='capture_image'),
    path('live_camera_feed/', views.live_camera_feed, name='live_camera_feed'),
    path('profile/', views.studentProfile, name='profile'),
    path('changePassword/', views.changePassword, name='changePassword'),
    path('logout/', views.studentLogout, name='logout'),
    path('scheduleSettings/', views.scheduleSettings, name='scheduleSettings'),
    path('success/', views.success, name='success'),
    path('loginSuccess/', views.loginSuccess, name='loginSuccess'),
    path('announcement/', views.announcement, name='announcement'),
    path('progressReport', views.progressReport, name='progressReport')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
