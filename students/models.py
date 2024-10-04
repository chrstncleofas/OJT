from django.db import models
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from app.models import CustomUser, RenderingHoursTable

class DataTableStudents(models.Model):
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
    status = models.CharField(max_length=50)
    archivedStudents = models.CharField(max_length=30, choices=ARCHIVED_STATUS, default='NotArchive')
    reset_token = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.Firstname} {self.Lastname}"
    
    def get_required_hours(self):
        try:
            course_requirement = RenderingHoursTable.objects.get(course=self.Course)
            return course_requirement.required_hours
        except RenderingHoursTable.DoesNotExist:
            return None
    
    def get_total_score(self):
        four_weeks_ago = timezone.now() - timedelta(weeks=4)

        # Calculate total score from TimeSheet
        total_time_sheet_score = TimeSheet.objects.filter(
            student=self,
            week_start_date__gte=four_weeks_ago
        ).aggregate(total_score=Sum('score'))['total_score'] or 0

        # Calculate total score from TableSubmittedReport
        total_report_score = TableSubmittedReport.objects.filter(
            student=self,
            date_submitted__gte=four_weeks_ago
        ).aggregate(total_score=Sum('report_file'))['total_score'] or 0

        # Calculate total score from TableSubmittedRequirement
        total_requirement_score = TableSubmittedRequirement.objects.filter(
            student=self
        ).aggregate(total_score=Sum('score'))['total_score'] or 0

        # Combine all scores
        total_score = total_time_sheet_score + total_report_score + total_requirement_score
        
        return total_score
        
class PendingApplication(models.Model):
    PendingStudentID = models.CharField(max_length=16, unique=True)
    PendingFirstname = models.CharField(max_length=100)
    PendingMiddlename = models.CharField(max_length=100, blank=True, null=True)
    PendingLastname = models.CharField(max_length=100)   
    PendingPrefix = models.CharField(max_length=100, blank=True, null=True)  
    PendingEmail = models.EmailField(unique=True)
    PendingAddress = models.CharField(max_length=250)
    PendingNumber = models.CharField(max_length=11)
    PendingCourse = models.CharField(max_length=100)
    PendingYear = models.CharField(max_length=50)
    PendingImage = models.ImageField(upload_to='profileImage/', blank=True, null=True)
    PendingUsername = models.CharField(max_length=100, unique=True)
    PendingPassword = models.CharField(max_length=100)
    StatusApplication = models.CharField(max_length=100, default='PendingApplication')
    PendingStatusArchive = models.CharField(max_length=100, default='NotArchive')

class RejectApplication(models.Model):
    RejectStudentID = models.CharField(max_length=16, unique=True)
    RejectFirstname = models.CharField(max_length=100)
    RejectMiddlename = models.CharField(max_length=100, blank=True, null=True)
    RejectLastname = models.CharField(max_length=100)   
    RejectPrefix = models.CharField(max_length=100, blank=True, null=True)  
    RejectEmail = models.EmailField(unique=True)
    RejectAddress = models.CharField(max_length=250)
    RejectNumber = models.CharField(max_length=11)
    RejectCourse = models.CharField(max_length=100)
    RejectYear = models.CharField(max_length=50)
    RejectUsername = models.CharField(max_length=100, unique=True)
    RejectPassword = models.CharField(max_length=100)
    RejectStatus = models.CharField(max_length=100, default='RejectedApplication')
    RejectStatusArchive = models.CharField(max_length=100, default='NotArchive')

class TimeLog(models.Model):
    ACTION_CHOICES = [
        ('IN', 'Time In'),
        ('OUT', 'Time Out'),
        ('LUNCH OUT', 'Lunch Out'),
        ('LUNCH IN', 'Lunch In'),
    ]
    
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
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

class TableSubmittedReport(models.Model):
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    date_submitted = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)

    def __str__(self):
        return f"Report by {self.student.username} on {self.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
class TimeSheet(models.Model):
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    week_start_date = models.DateField()
    score = models.IntegerField(default=0)
    submitted_file = models.FileField(upload_to='time_sheets/')

    def __str__(self):
        return f"TimeSheet for {self.student.username} starting {self.week_start_date}"
    
class TableSubmittedRequirement(models.Model):
    nameOfDocs = models.CharField(max_length=255)
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='student_submissions/')
    submission_date = models.DateTimeField(auto_now_add=True)

    due_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.student.username} - {self.nameOfDocs}"

    # Access student's email
    def get_student_email(self):
        return self.student.email

    # Access student's full name
    def get_student_fullname(self):
        return f"{self.student.first_name} {self.student.last_name}"

class ReturnToRevisionDocument(models.Model):
    nameOfDocs = models.CharField(max_length=255)
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    revision_file = models.FileField(upload_to='revision_documents/')
    return_date = models.DateTimeField(auto_now_add=True)
    revision_reason = models.TextField()

    def __str__(self):
        return f"{self.student.username} - {self.nameOfDocs} (Returned for Revision)"

    # Access student's email
    def get_student_email(self):
        return self.student.Email

    # Access student's full name
    def get_student_fullname(self):
        return f"{self.student.Firstname} {self.student.Lastname}"
    
class ApprovedDocument(models.Model):
    nameOfDocs = models.CharField(max_length=255)
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    approved_file = models.FileField(upload_to='approved_documents/')
    approved_date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.username} - {self.nameOfDocs} (Approved)"

class Grade(models.Model):
    student = models.ForeignKey(DataTableStudents, on_delete=models.CASCADE)
    evaluation = models.FloatField()
    docs = models.FloatField()
    oral_interview = models.FloatField()
    final_grade = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, default='No Remarks')

    @property
    def full_name(self):
        return f"{self.student.Firstname} {self.student.Lastname}"
    
    @property
    def course(self):
        return self.student.Course 

    @property
    def year(self):
        return self.student.Year

    def __str__(self):
        return f"Grade for {self.full_name}"
