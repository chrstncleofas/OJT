from superapp import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'superapp'

urlpatterns = [
    path('', views.superHome, name='superHome'),
    path('content/', views.postContent, name='content'),
    path('all-content', views.listOfContent, name='all-content'),
    path('editContent/<int:id>/', views.editContent, name='editContent'),
    path('deleteContent/<int:id>/', views.deleteContent, name='deleteContent'),
    path('viewStudent/<int:id>/', views.viewStudent, name='viewStudent'),
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
    path('getAllTheListAnnouncement/', views.getAllTheListAnnouncement, name='getAllTheListAnnouncement'),
    path('postAnnouncement/', views.postAnnouncement, name='postAnnouncement'),
    path('viewPendingApplication/<int:id>/', views.viewPendingApplication, name='viewPendingApplication'),
    path('editAnnouncement/<int:id>/', views.editAnnouncement, name='editAnnouncement'),
    path('deleteAnnouncement/<int:id>/', views.deleteAnnouncement, name='deleteAnnouncement'),
    path('deleteRequirementDocuments/<int:id>/', views.deleteRequirementDocuments, name='deleteRequirementDocuments'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
