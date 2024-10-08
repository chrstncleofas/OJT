import os
import fitz
from io import BytesIO
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.timezone import localtime
from django.shortcuts import render, redirect
from datetime import datetime, timedelta, time
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from app.models import TableAnnouncement, TableRequirements, TableContent
from students.models import DataTableStudents, TimeLog, Schedule, TableSubmittedReport, TableSubmittedRequirement, PendingApplication, ApprovedDocument, ReturnToRevisionDocument, LunchLog, Notification
from students.forms import ChangePasswordForm, StudentProfileForm, ScheduleSettingForm, FillUpPDFForm, SubmittedRequirement, PendingStudentRegistrationForm, TimeLogForm, ResetPasswordForm, LunchLogForm

@never_cache
@csrf_protect
def studentHome(request) -> HttpResponse:
    images = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/student-base.html',
        {
            'images': images
        }
    )

@never_cache
@csrf_protect
def studentDashboard(request) -> HttpResponse:
    images = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/student-dashboard.html',
        {
            'images': images
        }
    )

@login_required
@never_cache
def welcomeDashboard(request) -> HttpResponse:
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    images = TableContent.objects.all().order_by('id')
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    return render(
        request,
        'students/student-main-dashboard.html',
        {
            'firstName': firstName,
            'lastName': lastName,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'images': images
        }
    )

@never_cache
@csrf_protect
@login_required
def studentLogin(request):
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')
        pending_app = PendingApplication.objects.filter(PendingUsername=username, StatusApplication="PendingApplication").first()
        if pending_app:
            messages.warning(request, 'Your account is not yet approved. Please wait for admin approval.')
            return render(request, 'students/login.html')
        user = authenticate(request, username=username, password=password)
        
        if user:
            try:
                student = DataTableStudents.objects.get(user=user)
                if student.status == 'RejectedApplication':
                    messages.error(request, 'Your account has been rejected. Please contact the admin for further details.')
                    return render(request, 'students/login.html')
                elif student.archivedStudents == 'Archive':
                    messages.error(request, 'Your account has been locked due to inactivity. Please contact your admin.')
                    return render(request, 'students/login.html')
                if user.is_active:
                    login(request, user)
                    request.session['is_logged_in'] = True
                    return redirect('students:main-page')
                else:
                    messages.error(request, 'Your account is disabled.')
            
            except DataTableStudents.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'students/login.html')

def getAnnouncement(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'students/announcement.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

def getAnnouncementNotLogin(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'students/announcementNotLogin.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

def aboutPage(request):
    contents = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/about.html',
        {
            'contents': contents
        }
    )

def aboutLogin(request):
    contents = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/aboutLogin.html',
        {
            'contents': contents
        }
    )

@login_required
@never_cache
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
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
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
            'studentID': studentID,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    )

def mark_notification_as_read(request, id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=id)
        notification.is_read = True
        notification.save()
        return redirect('students:dashboard')
    return None

def draw_wrapped_text(page, text, start_pos, max_width, fontsize=12, fontname="helv"):
    """
    Draws wrapped text within the specified width on a given PDF page.

    :param page: The PyMuPDF page object.
    :param text: The text to be drawn.
    :param start_pos: Starting position (x, y) tuple for the text.
    :param max_width: Maximum width allowed for each line.
    :param fontsize: Font size for the text.
    :param fontname: Font name to be used.
    """
    x, y = start_pos
    rect = fitz.Rect(x, y, x + max_width, y + 1000)
    page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, align=0)

@login_required
@never_cache
def progressReport(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    full_name = f"{firstName} {lastName}"
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()

    if request.method == 'POST':
        form = FillUpPDFForm(request.POST)
        if form.is_valid():
            pdf_path = os.path.join(settings.PDF_ROOT, 'PROGRESS-REPORT.pdf')
            pdf_document = fitz.open(pdf_path)
            page = pdf_document[0]
            coordinates = {
                'name_field': (170, 157),
                'intern_name': (145, 707),
                'classification_local': (203, 185),
                'classification_international': (335, 185),
                'classification_in_campus': (225, 200),
                'classification_off_campus': (226, 215),
                'modality_actual': (204, 230),
                'modality_virtual': (335, 229),
                'virtual_wfh': (355, 245),
                'virtual_alternative': (355, 260),
                'hte_name': (170, 260),
                'hte_address': (170, 275),
                'department_division': (250, 290),
                'total_hours': (506, 652)
            }
            # Draw text fields
            page.insert_text(coordinates['name_field'], form.cleaned_data['student_name'], fontsize=12, color=(0, 0, 0))
            # Draw Internship Classification
            if form.cleaned_data['internship_classification'] == 'local':
                page.insert_text(coordinates['classification_local'], '✓', fontsize=45, color=(0, 0, 0))
            elif form.cleaned_data['internship_classification'] == 'international':
                page.insert_text(coordinates['classification_international'], '✓', fontsize=45, color=(0, 0, 0))
            # Draw Local Condition
            if form.cleaned_data['local_condition'] == 'inCampus':
                page.insert_text(coordinates['classification_in_campus'], '✓', fontsize=45, color=(0, 0, 0))
            elif form.cleaned_data['local_condition'] == 'offCampus':
                page.insert_text(coordinates['classification_off_campus'], '✓', fontsize=45, color=(0, 0, 0))
            # Draw Modality
            if form.cleaned_data['internship_modality'] == 'actual':
                page.insert_text(coordinates['modality_actual'], '✓', fontsize=45, color=(0, 0, 0))
            elif form.cleaned_data['internship_modality'] == 'virtual':
                page.insert_text(coordinates['modality_virtual'], '✓', fontsize=45, color=(0, 0, 0))
            # Draw Virtual
            if form.cleaned_data['virtual_conditions'] == 'wfh':
                page.insert_text(coordinates['virtual_wfh'], '✓', fontsize=45, color=(0, 0, 0))
            elif form.cleaned_data['virtual_conditions'] == 'under':
                page.insert_text(coordinates['virtual_alternative'], '✓', fontsize=45, color=(0, 0, 0))
            # Draw 
            page.insert_text(coordinates['hte_name'], form.cleaned_data['hte_name'], fontsize=12, color=(0, 0, 0))
            page.insert_text(coordinates['hte_address'], form.cleaned_data['hte_address'], fontsize=12, color=(0, 0, 0))
            page.insert_text(coordinates['department_division'], form.cleaned_data['department_division'], fontsize=12, color=(0, 0, 0))
            page.insert_text(coordinates['intern_name'], form.cleaned_data['student_name'], fontsize=12, color=(0, 0, 0))
            text_fontsize = 9
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            y_start = 350
            description_max_width = 265
            total_hours = 0
            for day in days:
                date = form.cleaned_data.get(f'{day}_date')
                description = form.cleaned_data.get(f'{day}_description')
                hours = form.cleaned_data.get(f'{day}_hours')
                if date:
                    page.insert_text((140, y_start + 20), date.strftime('%Y-%m-%d'), fontsize=text_fontsize, color=(0, 0, 0))
                if description:
                    draw_wrapped_text(page, description, (205, y_start - 5), description_max_width, fontsize=text_fontsize)           
                if hours:
                    page.insert_text((500, y_start + 15), str(hours), fontsize=text_fontsize, color=(0, 0, 0))
                    total_hours += hours        
                y_start += 60
            # 
            page.insert_text(coordinates['total_hours'], str(total_hours), fontsize=text_fontsize, color=(0, 0, 0))
            # 
            buffer = BytesIO()
            pdf_document.save(buffer)
            pdf_document.close()
            buffer.seek(0)

            if not buffer.getvalue():
                messages.error(request, "PDF generation failed.")
                return redirect('students:progressReport')

            action = request.POST.get('action')
            if action == 'preview_report':
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="PROGRESS-REPORT.pdf"'
                return response
            elif action == 'submit_report':
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                file_name = f"{timestamp}_PROGRESS-REPORT.pdf"
                report_instance = TableSubmittedReport.objects.create(student=student)
                report_instance.report_file.save(file_name, buffer)

                messages.success(request, "Report submitted successfully!")
                return redirect('students:progressReport')

    else:
        form = FillUpPDFForm()    
    return render(
        request, 
        'students/progress-report.html', 
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    )

@login_required
@never_cache
def exportTimeLogToPDF(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    time_logs = TimeLog.objects.filter(
        student=student,
        timestamp__week_day__in=[1, 2, 3, 4, 5, 6, 7]
    ).order_by('timestamp')
    lunch_logs = LunchLog.objects.filter(student=student).order_by('timestamp')
    buffer = BytesIO()
    pdf_document = fitz.open(os.path.join(settings.PDF_ROOT, 'INTERNSHIP-TIME-SHEET.pdf'))
    page = pdf_document[0]
    y_position = 100
    last_time_in = None
    last_lunch_out = None
    total_hours_for_week = timedelta()
    for log in time_logs:
        local_time = timezone.localtime(log.timestamp)
        time_formatted = local_time.strftime('%I:%M %p')
        date = log.timestamp.strftime('%Y-%m-%d')
        if log.action == 'IN':
            last_time_in = local_time
        elif log.action == 'OUT' and last_time_in:
            duration = local_time - last_time_in
            total_hours_for_week += duration
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            total_duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            page.insert_text((105, y_position + 220), date, fontsize=9, color=(0, 0, 0))  # Date
            page.insert_text((160, y_position + 220), last_time_in.strftime('%I:%M %p'), fontsize=9, color=(0, 0, 0))
            page.insert_text((385, y_position + 220), time_formatted, fontsize=9, color=(0, 0, 0))
            page.insert_text((477, y_position + 220), total_duration_str, fontsize=9, color=(0, 0, 0))

            lunch_in_log = lunch_logs.filter(timestamp__gt=last_time_in, timestamp__lt=local_time, action='LUNCH IN').first()
            lunch_out_log = lunch_logs.filter(timestamp__gt=last_time_in, timestamp__lt=local_time, action='LUNCH OUT').first()

            if lunch_out_log:
                lunch_out_time = timezone.localtime(lunch_out_log.timestamp).strftime('%I:%M %p')
                page.insert_text((250, y_position + 220), lunch_out_time, fontsize=9, color=(0, 0, 0))

            if lunch_in_log:
                lunch_in_time = timezone.localtime(lunch_in_log.timestamp).strftime('%I:%M %p')
                page.insert_text((320, y_position + 220), lunch_in_time, fontsize=9, color=(0, 0, 0))

            y_position += 20
            last_time_in = None
    start_month = 4
    end_month = 6
    current_year = datetime.now().year
    months = ", ".join([datetime(current_year, month, 1).strftime("%B") for month in range(start_month, end_month + 1)])
    quarter = "Q2"
    fullname = f"{student.Firstname} {student.Lastname}"
    page.insert_text((140, 245), fullname, fontsize=12, color=(0, 0, 0))
    page.insert_text((170, 205), quarter, fontsize=12, color=(0, 0, 0))
    page.insert_text((429, 205), months, fontsize=12, color=(0, 0, 0))
    total_week_hours = total_hours_for_week.seconds // 3600
    total_week_minutes = (total_hours_for_week.seconds % 3600) // 60
    total_week_str = f"{total_week_hours}h {total_week_minutes}m" if total_week_minutes > 0 else f"{total_week_hours}h"
    page.insert_text((462, y_position + 455), total_week_str, fontsize=12, color=(0, 0, 0))
    pdf_document.save(buffer)
    pdf_document.close()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{fullname} - TimeSheet.pdf"'
    return response

@login_required
@never_cache
def log_lunch(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    requirements_submitted = ApprovedDocument.objects.filter(student=student).exists()
    if not requirements_submitted:
        message = 'Please wait for the admin to approve your document before you can time in and time out.'
        return render(
            request,
            'students/timeIn-timeOut.html',
            {
                'message': message,
                'forms': LunchLogForm(),
                'requirements_submitted': requirements_submitted,
            }
        )
    if request.method == 'POST':
        forms = LunchLogForm(request.POST, request.FILES)      
        if forms.is_valid():
            lunch_log = forms.save(commit=False)
            lunch_log.student = student
            lunch_log.save()
            return redirect('students:clockin')
    else:
        forms = LunchLogForm()
    return render(request, 'students/timeIn-timeOut.html', {'forms': forms})

@login_required
@never_cache
def TimeInAndTimeOut(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    schedule_exists = Schedule.objects.filter(student=student).exists()
    requirements_submitted = ApprovedDocument.objects.filter(student=student).exists()
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    if not requirements_submitted:
        message = 'Please wait for the admin to approve your document before you can time in and time out.'
        return render(
            request,
            'students/timeIn-timeOut.html',
            {
                'firstName': student.Firstname,
                'lastName': student.Lastname,
                'message': message,
                'form': TimeLogForm(),
                'schedule_exists': schedule_exists,
                'requirements_submitted': requirements_submitted,
                'notifications': notifications,
                'unread_notifications_count': unread_notifications_count,
            }
        )
    if request.method == 'POST':
        form = TimeLogForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            student = get_object_or_404(DataTableStudents, user=user)
            time_log = form.save(commit=False)
            time_log.student = student
            time_log.timestamp = timezone.now()
            time_log.save()
            return redirect('students:clockin')
    else:
        form = TimeLogForm()
    time_logs = TimeLog.objects.filter(student=student).order_by('timestamp')
    daily_total = timedelta()
    paired_logs = []
    lunch_logs = LunchLog.objects.filter(student=student).order_by('timestamp')
    max_work_hours = timedelta(hours=8)
    i = 0
    while i < len(time_logs):
        if time_logs[i].action == 'IN':
            if i + 1 < len(time_logs) and time_logs[i + 1].action == 'OUT':
                time_in = time_logs[i].timestamp
                time_out = time_logs[i + 1].timestamp
                work_period = time_out - time_in
                work_period = min(work_period, max_work_hours)
                daily_total += work_period
                paired_logs.append((time_logs[i], time_logs[i + 1]))
                i += 1
        i += 1
    total_work_seconds = max(0, daily_total.total_seconds())
    required_hours_seconds = student.get_required_hours() * 3600 if student.get_required_hours() is not None else 0
    remaining_hours_seconds = max(0, required_hours_seconds - total_work_seconds)
    def format_seconds(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes"
    last_log = TimeLog.objects.filter(student=student).order_by('-timestamp').first()
    last_action = last_log.action if last_log else ''
    current_time = timezone.localtime(timezone.now())
    full_schedule = Schedule.objects.filter(student=student, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('id')
    return render(
        request,
        'students/timeIn-timeOut.html',
        {
            'required_hours_seconds': required_hours_seconds,
            'remaining_hours_seconds': remaining_hours_seconds,
            'total_work_time': format_seconds(total_work_seconds),
            'required_hours_time': format_seconds(required_hours_seconds),
            'remaining_hours_time': format_seconds(remaining_hours_seconds),
            'firstName': student.Firstname,
            'lastName': student.Lastname,
            'time_logs': paired_logs,
            'lunch_logs': lunch_logs,
            'current_time': current_time,
            'form': form,
            'full_schedule': full_schedule,
            'last_action': last_action,
            'schedule_exists': schedule_exists,
            'requirements_submitted': requirements_submitted,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    )

@login_required
@never_cache
def studentProfile(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('students:dashboard')
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
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    })

@login_required
@never_cache
def changePassword(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
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
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        }
    )

@never_cache
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = DataTableStudents.objects.filter(Email=email).first()
        if user:
            token = get_random_string(32)
            user.reset_token = token
            user.save()
            reset_link = request.build_absolute_uri(reverse('students:reset_password', args=[token]))
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('students:login')
        else:
            messages.error(request, 'Email not found.')
    return render(request, 'students/forgot_password.html')

@never_cache
def reset_password(request, token):
    user = get_object_or_404(DataTableStudents, reset_token=token).user
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.password = make_password(new_password)
            user.reset_token = None
            user.save()
            messages.success(request, 'Your password has been reset successfully.')
            return redirect('students:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResetPasswordForm()
    return render(request, 'students/reset_password.html', {'form': form, 'token': token})

@never_cache
def studentRegister(request):
    if request.method == 'POST':
        pending_registration_form = PendingStudentRegistrationForm(request.POST)
        if pending_registration_form.is_valid():
            studentId = pending_registration_form.cleaned_data['PendingStudentID']
            email = pending_registration_form.cleaned_data['PendingEmail']
            username = pending_registration_form.cleaned_data['PendingUsername']
            phone_number = pending_registration_form.cleaned_data['PendingNumber']  # Kunin ang phone number
            if DataTableStudents.objects.filter(Email=email).exists():
                messages.error(request, "Email already exists.")
            elif DataTableStudents.objects.filter(Username=username).exists():
                messages.error(request, "Username already exists.")
            elif DataTableStudents.objects.filter(StudentID=studentId).exists():
                messages.error(request, "Student ID already exists.")
            else:
                pending_registration = PendingApplication(
                    PendingEmail=email,
                    PendingUsername=username,
                    PendingPassword=pending_registration_form.cleaned_data['PendingPassword'],
                    PendingFirstname=pending_registration_form.cleaned_data['PendingFirstname'],
                    PendingMiddlename=pending_registration_form.cleaned_data.get('PendingMiddlename', ''),
                    PendingLastname=pending_registration_form.cleaned_data['PendingLastname'],
                    PendingPrefix=pending_registration_form.cleaned_data.get('PendingPrefix', ''),
                    PendingStudentID=pending_registration_form.cleaned_data['PendingStudentID'],
                    PendingAddress=pending_registration_form.cleaned_data['PendingAddress'],
                    PendingNumber=phone_number,
                    PendingCourse=pending_registration_form.cleaned_data['PendingCourse'],
                    PendingYear=pending_registration_form.cleaned_data['PendingYear'],
                )
                pending_registration.save()
                
                subject = 'Registration Pending Approval'
                message = render_to_string('students/registration_email.txt', {
                    'first_name': pending_registration.PendingFirstname,
                    'last_name': pending_registration.PendingLastname,
                    'email': pending_registration.PendingEmail,
                    'username': pending_registration.PendingUsername,
                })

                # Padala ang email
                recipient_list = [pending_registration.PendingEmail]
                send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
                
                # Padala ang SMS notification
                # sms_message = f"Hello {pending_registration.PendingFirstname}, your registration is pending approval."
                # send_sms(phone_number, sms_message)

                messages.success(request, "Your registration is pending approval by the admin.")
                return redirect('students:register')
    else:
        pending_registration_form = PendingStudentRegistrationForm()

    return render(
        request, 'students/register.html', 
        {
            'pending_registration_form': pending_registration_form
        }
    )

@login_required
@never_cache
def requirements(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    if request.method == 'POST':
        form = SubmittedRequirement(request.POST, request.FILES, student=student)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = student
            submission.save()
            return HttpResponseRedirect(reverse('students:requirements'))
    form = SubmittedRequirement(student=student)

    required_docs = ['Application Form', 'Parent Consent', 'Notice of Acceptance / MOA', 
                     'Endorsement Letter', 'Internship Contract Agreement', 'Medical Certificate', 'Evaluation Form',
                     'Progress Report', 'Internship Time Sheet', 'Internship Exit Survey', 'Student Performance Evaluation',
                     'Supporting Document of Time Sheet', 'Supporting Document of Progress Report']

    requirements = TableRequirements.objects.all().order_by('id')
    submitted_docs = TableSubmittedRequirement.objects.filter(student=student).values_list('nameOfDocs', flat=True)
    remaining_docs = [doc for doc in required_docs if doc not in submitted_docs]
    return render(request, 'students/requirements.html', {
        'form': form,
        'remaining_docs': remaining_docs,
        'requirements': requirements,
        'firstName': student.Firstname,
        'lastName': student.Lastname,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    })

@never_cache
@csrf_protect
def studentLogin(request):
    if request.user.is_authenticated:
        return redirect('students:main-page')
    
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')

        # Check if the user has a pending application
        pending_app = PendingApplication.objects.filter(PendingUsername=username, StatusApplication="PendingApplication").first()
        if pending_app:
            messages.warning(request, 'Your account is not yet approved. Please wait for admin approval.')
            return render(request, 'students/login.html')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user:
            try:
                # Get the student linked to the authenticated user
                student = DataTableStudents.objects.get(user=user)

                # Check the student's application status
                if student.status == 'RejectedApplication':
                    messages.error(request, 'Your account has been rejected. Please contact the admin for further details.')
                    return render(request, 'students/login.html')
                elif student.archivedStudents == 'Archive':
                    messages.error(request, 'Your account has been locked due to inactivity. Please contact your admin.')
                    return render(request, 'students/login.html')
                
                # Log in the user if they are active
                if user.is_active:
                    login(request, user)
                    request.session['is_logged_in'] = True
                    return redirect('students:main-page')
                else:
                    messages.error(request, 'Your account is disabled.')
            
            except DataTableStudents.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'students/login.html')

def studentLogout(request) -> HttpResponseRedirect:
    logout(request)
    return redirect('students:login')

@login_required
@never_cache
def scheduleSettings(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    if request.method == 'POST':
        form = ScheduleSettingForm(request.POST)
        if form.is_valid():
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

            return redirect('students:schedule')
    else:
        form = ScheduleSettingForm()

    return render(request, 'students/settings.html', {
        'form': form,
        'firstName' : firstName,
        'lastName' : lastName,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    })

@login_required
@never_cache
def getAllSubmittedDocuments(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    progress_report = TableSubmittedReport.objects.filter(student=student).order_by('-date_submitted', 'id')
    submittedDocs = ApprovedDocument.objects.filter(student=student)
    revision = ReturnToRevisionDocument.objects.filter(student=student)
    return render(request, 'students/submitted-docs.html', {
        'firstName' : firstName,
        'lastName' : lastName,
        'progress_report': progress_report,
        'submittedDocs': submittedDocs,
        'revision': revision,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    })
