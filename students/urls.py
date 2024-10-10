from students import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'students'

urlpatterns = [
    path('', views.studentHome, name='home'),
    path('about/', views.aboutPage, name='about'),
    path('login', views.studentLogin, name='login'),
    path('logout/', views.studentLogout, name='logout'),
    path('profile/', views.studentProfile, name='profile'),
    path('clockin/', views.ClockInAndOut, name='clockin'),
    path('about-page/', views.aboutLogin, name='about-page'),
    path('register/', views.studentRegister, name='register'),
    path('schedule/', views.scheduleSettings, name='schedule'),
    path('download/', views.exportTimeLogToPDF, name='download'),
    path('main-page/', views.welcomeDashboard, name='main-page'),
    path('requirements/', views.requirements, name='requirements'),
    path('log_lunch/', views.log_lunch, name='log_lunch'),
    path('dashboard/', views.mainPageForDashboard, name='dashboard'),
    path('announcement/', views.getAnnouncement, name='announcement'),
    path('progress-report', views.typeTheDetailsProgressReportPdf, name='progress-report'),
    path('documents/', views.getAllSubmittedDocuments, name='documents'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('changePassword/', views.changePassword, name='changePassword'),
    path('reset_password/<str:token>/', views.reset_password, name='reset_password'),
    path('announcement-page/', views.getAnnouncementNotLogin, name='announcement-page'),
    path('mark-notification-as-read/<int:id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
