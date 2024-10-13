from homepage import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'homepage'

urlpatterns = [
    path('', views.homePage, name='home'),
    path('announcement', views.getAnnouncement, name='announcement'),
    path('students/login/', views.studentLogin, name='student_login'),
    path('coordinator/login/', views.coordinatorLogin, name='coordinator_login'),
    path('student-register', views.studentRegister, name='student-register'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<str:token>/', views.reset_password, name='reset_password'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
