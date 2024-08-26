import uuid
import base64
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from app.models import CustomUser, RenderingHoursTable

class DataTableStudents(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    ARCHIVED_STATUS = [
        ('NotArchive', 'NotArchive'),
        ('Archive', 'Archive'),
        ('UnArchive', 'Unarchive'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    StudentID = models.CharField(max_length=16, unique=True)
    Firstname = models.CharField(max_length=100)
    Middlename = models.CharField(max_length=100, blank=True, null=True)
    Lastname = models.CharField(max_length=100)   
    Prefix = models.CharField(max_length=100, blank=True, null=True)  
    Email = models.EmailField(unique=True)
    Address = models.CharField(max_length=250)
    Number = models.CharField(max_length=11)
    Course = models.CharField(max_length=100)
    Year = models.CharField(max_length=50)
    Image = models.ImageField(upload_to='profileImage/', blank=True, null=True)
    Username = models.CharField(max_length=100, unique=True)
    Password = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    archivedStudents = models.CharField(max_length=30, choices=ARCHIVED_STATUS, default='NotArchive')

    def __str__(self):
        return f"{self.Firstname} {self.Lastname}"
    
    def get_required_hours(self):
        try:
            course_requirement = RenderingHoursTable.objects.get(course=self.Course)
            return course_requirement.required_hours
        except RenderingHoursTable.DoesNotExist:
            return None

class TimeLog(models.Model):
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=[('IN', 'Time In'), ('OUT', 'Time Out')])
    timestamp = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='time_logs/', blank=True, null=True)
    duration = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.student} - {self.action} at {self.timestamp}"
    
class Schedule(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.student.username} - {self.day}"
