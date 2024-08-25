from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from app.models import TableAnnouncement
from io import BytesIO
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.core.files.base import ContentFile
import base64
import logging
import cv2
import numpy as np
from django.utils.timezone import now
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from students.models import DataTableStudents, TimeLog, Schedule
from students.forms import StudentRegistrationForm, UserForm, ChangePasswordForm, TimeLogForm, StudentProfileForm, ScheduleSettingForm

logger = logging.getLogger(__name__)

def studentHome(request) -> HttpResponse:
    return render(request, 'students/student-base.html')

def studentDashboard(request) -> HttpResponse:
    return render(request, 'students/student-dashboard.html')

@login_required
def welcomeDashboard(request) -> HttpResponse:
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    return render(
        request,
        'students/student-main-dashboard.html',
        {
            'firstName': firstName,
            'lastName': lastName,
        }
    )

def announcement(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'students/announcement.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

def mainPageForDashboard(request) -> HttpResponse:
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    # 
    studentID = student.StudentID
    firstName = student.Firstname
    lastName = student.Lastname
    email = student.Email
    course = student.Course
    year = student.Year
    # 
    return render(
        request,
        'students/student-dashboard.html',
        {
            'firstName': firstName,
            'lastName': lastName,
            'email': email,
            'course': course,
            'year': year,
            'student': student,
            'studentID': studentID
        }
    )

def video_stream():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to JPEG format
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def live_camera_feed(request):
    return StreamingHttpResponse(video_stream(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

logger = logging.getLogger(__name__)

def capture_image(request):
    if request.method == 'POST':
        try:
            # Initialize the camera
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                raise Exception('Failed to capture image')

            # Convert image to PNG format
            is_success, buffer = cv2.imencode(".png", frame)
            io_buf = BytesIO(buffer)
            image_data = io_buf.getvalue()

            # Create an in-memory file
            image_file = ContentFile(image_data, 'captured_image.png')

            # Get the current user
            user = request.user
            student = DataTableStudents.objects.get(user=user)

            # Save image to TimeLog
            time_log = TimeLog(student=student, image=image_file)
            time_log.save()
            image_url = time_log.image.url

            return JsonResponse({'image_url': image_url})
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def TimeInAndTimeOut(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    time_logs = TimeLog.objects.filter(student=student).order_by('-timestamp')
    full_schedule = Schedule.objects.filter(student=student).order_by('day')

    if request.method == 'POST':
        action = request.POST.get('action')
        form = TimeLogForm(request.POST, request.FILES)
        
        if form.is_valid():
            timestamp = timezone.now()
            time_log = form.save(commit=False)
            time_log.student = student
            time_log.timestamp = timestamp

            if action == 'IN':
                last_time_in = TimeLog.objects.filter(student=student, action='IN').order_by('-timestamp').first()
                last_time_out = TimeLog.objects.filter(student=student, action='OUT').order_by('-timestamp').first()

                if last_time_in and (not last_time_out or last_time_in.timestamp > last_time_out.timestamp):
                    messages.error(request, 'You have already timed in and not timed out yet.')
                    return redirect('students:TimeInAndTimeOut')

                time_log.save()
                messages.success(request, 'Time In recorded successfully.')

            elif action == 'OUT':
                last_time_in = TimeLog.objects.filter(student=student, action='IN').order_by('-timestamp').first()

                if not last_time_in:
                    messages.error(request, 'No corresponding Time In found. Please Time In first.')
                    return redirect('students:TimeInAndTimeOut')

                if time_logs and time_logs.first().action == 'OUT':
                    messages.error(request, 'You have already timed out. Please Time In first.')
                    return redirect('students:TimeInAndTimeOut')

                # Calculate duration
                time_diff = timestamp - last_time_in.timestamp
                duration_hours = round(time_diff.total_seconds() / 3600, 2)
                time_log.duration = duration_hours
                time_log.save()
                messages.success(request, 'Time Out recorded successfully.')

            return redirect('students:TimeInAndTimeOut')
        else:
            messages.error(request, 'Invalid form submission. Please try again.')
            return redirect('students:TimeInAndTimeOut')
    else:
        form = TimeLogForm()

    context = {
        'form': form,
        'time_logs': time_logs,
        'full_schedule': full_schedule,
    }
    return render(request, 'students/timeIn-timeOut.html', context)



def studentProfile(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('students:Dashboard')
    else:
        form = StudentProfileForm(instance=student)

    return render(request, 'students/student-profile.html', {
        'form': form,
        'firstName': student.Firstname,
        'lastName': student.Lastname,
        'email': student.Email,
        'course': student.Course,
        'year': student.Year,
        'student': student,
    })

def changePassword(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data['current_password']
            new_password = form.cleaned_data['new_password']            
            if check_password(current_password, user.password):
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                return redirect('students:changePassword')
            else:
                messages.error(request, 'Your current password was entered incorrectly. Please enter it again.')
    else:
        form = ChangePasswordForm()
    
    return render(
        request,
        'students/changePassword.html',
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName,

        }
    )

def studentRegister(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)
        if user_form.is_valid() and student_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            student = student_form.save(commit=False)
            student.user = user
            student.StudentID = student_form.cleaned_data['StudentID']
            student.Email = user.email
            student.Username = user.username
            student.Password = user.password
            student.save()

            # Sending email notification
            subject = 'Registration Successful'
            message = render_to_string('students/registration_email.txt', {
                'first_name': student.Firstname,
                'last_name': student.Lastname,
                'email': student.Email,
                'username': student.Username,
            })
            recipient_list = [student.Email]
            send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)

            messages.success(request, "Registration successful, Your account is pending approval by an admin, Please wait for admin's approve your account...")
            return redirect('students:success')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        user_form = UserForm()
        student_form = StudentRegistrationForm()

    return render(request, 'students/register.html', {'user_form': user_form, 'student_form': student_form})

def studentLogin(request):
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                student = DataTableStudents.objects.get(user=user)
                if student.status == 'pending':
                    messages.warning(request, 'Your account is not approved yet. Please wait for admin approval.')
                    return render(request, 'students/login.html')
                elif student.status == 'rejected':
                    messages.error(request, 'Your account has been rejected. Please contact the admin for further details.')
                    return render(request, 'students/login.html')
                elif student.archivedStudents == 'Archive':
                    messages.error(request, 'Your account has been lock due to inactivity level. Please contact your admin.')
                    return render(request, 'students/login.html')
                else:
                    if user.is_active:
                        login(request, user)
                        return redirect('students:studentPage')
                    else:
                        messages.error(request, 'Your account is disabled.')
            except DataTableStudents.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'students/login.html')

def success(request):
    return render(request, 'students/success.html')

def loginSuccess(request):
    return render(request, 'students/loginSuccess.html')

def studentLogout(request) -> HttpResponseRedirect:
    logout(request)
    return redirect(reverse('students:home'))

def scheduleSettings(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    if request.method == 'POST':
        form = ScheduleSettingForm(request.POST)
        if form.is_valid():
            # Clearing existing schedule for the student
            Schedule.objects.filter(student=student).delete()

            days_times = {
                'Monday': ('monday_start', 'monday_end'),
                'Tuesday': ('tuesday_start', 'tuesday_end'),
                'Wednesday': ('wednesday_start', 'wednesday_end'),
                'Thursday': ('thursday_start', 'thursday_end'),
                'Friday': ('friday_start', 'friday_end'),
            }

            for day, (start_field, end_field) in days_times.items():
                start_time = form.cleaned_data[start_field]
                end_time = form.cleaned_data[end_field]
                if start_time and end_time:
                    Schedule.objects.create(
                        student=student,
                        day=day,
                        start_time=start_time,
                        end_time=end_time
                    )

            return redirect('students:scheduleSettings')
    else:
        form = ScheduleSettingForm()

    return render(request, 'students/settings.html', {
        'form': form,
        'firstName' : firstName,
        'lastName' : lastName
    })
