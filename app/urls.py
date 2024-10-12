from app import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('', views.home, name='home'),
    # path('login', views.userLoginFunction, name='login'),
    path('register/', views.register, name='register'),
    path('profile', views.profile, name='profile'),
    path('logout', views.logoutView, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('content/', views.postContent, name='content'),
    path('student-logs/<int:id>/', views.studentInformation, name='student-logs'),
    # 
    path('changePass', views.changePass, name='changePass'),
    path('mainDashboard', views.mainDashboard, name='mainDashboard'),
    path('studentManagement', views.studentManagement, name='studentManagement'),
    path('editStudentDetails/<int:id>/', views.editStudentDetails, name='editStudentDetails'),
    # 
    path('approve_student/<int:id>/', views.approveStudent, name='approve_student'),
    path('reject_students/<int:id>/', views.rejectStudent, name='reject_students'),
    # 
    path('archivedStudent/<int:id>/', views.archivedStudent, name='archivedStudent'),
    path('get_admin_password_hash/', views.getAdminPasswordHash, name='get_admin_password_hash'),
    path('validate_admin_password/', views.validateAdminPassword, name='validate_admin_password'),
    
    path('unArchivedStudent/<int:id>/', views.unArchivedStudent, name='unArchivedStudent'),
    # 
    path('viewPendingApplication/<int:id>/', views.viewPendingApplication, name='viewPendingApplication'),
    path('setSchedule/<int:id>/', views.setSchedule, name='setSchedule'),
    # 
    path('announcement', views.postAnnouncement, name='announcement'),
    path('listOfAnnouncement', views.listOfAnnouncement, name='listOfAnnouncement'),
    path('all-content', views.listOfContent, name='all-content'),
    path('grading', views.getAllStudentsForGrading, name='grading'),
    path('submission', views.getTheSubmitRequirements, name='submission'),
    path('editAnnouncement/<int:id>/', views.editAnnouncement, name='editAnnouncement'),
    path('editContent/<int:id>/', views.editContent, name='editContent'),
    path('deleteAnnouncement/<int:id>/', views.deleteAnnouncement, name='deleteAnnouncement'),
    path('deleteContent/<int:id>/', views.deleteContent, name='deleteContent'),
    path('deleteRequirementDocuments/<int:id>/', views.deleteRequirementDocuments, name='deleteRequirementDocuments'),
    path('gradeCalculator/<int:id>/', views.gradeCalculator, name='gradeCalculator'),
    #
    path('set_rendering_hours/', views.set_rendering_hours, name='set_rendering_hours'),
    path('announcementNotLogin/', views.getAnnouncementNotLogin, name='announcementNotLogin'),
    path('announcementLogin/', views.getAnnouncement, name='announcementLogin'),
    path('return_to_revision/<int:id>/', views.return_to_revision, name='return_to_revision'),
    path('approve_document/<int:id>/', views.approve_document, name='approve_document'),
    path('update_document_score/<int:id>/', views.update_document_score, name='update_document_score'),
    path('view-requirements/<int:id>/', views.submittedRequirementOfStudents, name='view-requirements'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_URL)