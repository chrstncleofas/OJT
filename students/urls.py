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
    path('announcement/', views.getAnnouncement, name='announcement'),
    path('dashboard/', views.mainPageForDashboard, name='dashboard'),
    path('main-page/', views.welcomeDashboard, name='main-page'),
    path('progressReport', views.progressReport, name='progressReport'),
    path('changePassword/', views.changePassword, name='changePassword'),
    path('clockin/', views.TimeInAndTimeOut, name='clockin'),
    path('schedule/', views.scheduleSettings, name='schedule'),
    path('requirements/', views.requirements, name='requirements'),
    path('documents/', views.getAllSubmittedDocuments, name='documents'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
