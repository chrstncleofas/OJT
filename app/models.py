from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    position = models.CharField(max_length=100)

class RenderingHoursTable(models.Model):
    COURSE_CHOICES = [
        ('BS Information Technology', 'BS Information Technology'),
        ('BS Computer Science', 'BS Computer Science'),
    ]
    
    course = models.CharField(max_length=100, choices=COURSE_CHOICES, unique=True)
    required_hours = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.course} - {self.required_hours} hours"

class TableAnnouncement(models.Model):
    Title = models.CharField(max_length=100)
    Image = models.ImageField(upload_to='announcement/', blank=True, null=True)
    StartDate = models.DateTimeField()
    EndDate = models.DateTimeField()
    Description = models.CharField(max_length=450)
    Status = models.CharField(max_length=100)

class StoreActivityLogs(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp} from {self.ip_address}"
    
class TableRequirements(models.Model):
    nameOfFile = models.CharField(max_length=255)
    document = models.FileField(upload_to='ojt_requirements/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nameOfFile

class TableContent(models.Model):
    nameOfContent = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.FileField(upload_to='content/')
    uploadDate = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nameOfContent
