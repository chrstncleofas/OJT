from students import views
from django.urls import path

app_name = 'students'

urlpatterns = [
    path('', views.studentHome, name='home'),
]
