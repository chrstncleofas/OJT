from students import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'students'

urlpatterns = [
    path('', views.studentHome, name='home'),
    path('login', views.studentLogin, name='login'),
    path('logout/', views.studentLogout, name='logout'),
    path('profile/', views.studentProfile, name='profile'),
    path('register/', views.studentRegister, name='register'),
    path('dashboard/', views.studentDashboard, name='dashboard'),
    path('announcement/', views.getAnnouncement, name='announcement'),
    path('Dashboard/', views.mainPageForDashboard, name='Dashboard'),
    path('studentPage/', views.welcomeDashboard, name='studentPage'),
    path('progressReport', views.progressReport, name='progressReport'),
    path('changePassword/', views.changePassword, name='changePassword'),
    path('TimeInAndTimeOut/', views.TimeInAndTimeOut, name='TimeInAndTimeOut'),
    path('scheduleSettings/', views.scheduleSettings, name='scheduleSettings'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
