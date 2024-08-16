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

class Announcement(models.Model):
    Title = models.CharField(max_length=100)
    Image = models.ImageField(upload_to='announcement/', blank=True, null=True)
    Category = models.CharField(max_length=150, blank=True, null=True)
    Date = models.DateField()
    Description = models.CharField(max_length=450)
    Status = models.CharField(max_length=100)
