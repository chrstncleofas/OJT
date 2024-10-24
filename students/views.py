import os
import fitz
from io import BytesIO
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.hashers import check_password, make_password
from app.models import TableAnnouncement, TableRequirements, TableContent
from students.models import DataTableStudents, TimeLog, Schedule, TableSubmittedReport, TableSubmittedRequirement, PendingApplication, ApprovedDocument, ReturnToRevisionDocument, LunchLog, Notification
from students.forms import ChangePasswordForm, StudentProfileForm, ScheduleSettingForm, ProgressReportForm, SubmittedRequirement, PendingStudentRegistrationForm, TimeLogForm, ResetPasswordForm, LunchLogForm

@never_cache
@login_required
@csrf_exempt
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
@login_required
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
@csrf_protect
@cache_control(no_cache=True, must_revalidate=True, no_store=True, name='dispatch')
def welcomeDashboard(request) -> HttpResponse:
    # Check if the user is NOT a staff or a superuser
    if request.user.is_staff or request.user.is_superuser:
        return render(request, 'main/404.html', status=403)  
    # Proceed if the user is a student
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
@login_required
@csrf_exempt
def getAnnouncement(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'students/announcement.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

@never_cache
@login_required
@csrf_exempt
def getAnnouncementNotLogin(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'students/announcementNotLogin.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

@never_cache
@login_required
@csrf_exempt
def aboutPage(request):
    contents = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/about.html',
        {
            'contents': contents
        }
    )

@never_cache
@login_required
@csrf_exempt
def aboutLogin(request):
    contents = TableContent.objects.all().order_by('id')
    return render(
        request, 'students/aboutLogin.html',
        {
            'contents': contents
        }
    )

@never_cache
@login_required
@csrf_exempt
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

def typeTheDetailsProgressReportPdf(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname or ''
    middleName = student.Middlename or ''
    lastName = student.Lastname or ''
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    full_name = f"{firstName} {middleName} {lastName}".strip()
    # Calculate total work hours for each day in the current week
    current_date = timezone.now().date()
    week_start = current_date - timedelta(days=current_date.weekday())
    week_end = week_start + timedelta(days=6)
    work_hours_per_day = {
        'monday': 0,
        'tuesday': 0,
        'wednesday': 0,
        'thursday': 0,
        'friday': 0,
    }
    # Retrieve time logs for the current week for the student
    time_logs = TimeLog.objects.filter(student=student, timestamp__date__range=[week_start, week_end]).order_by('timestamp')
    # Calculate work hours per day from the time logs
    for i in range(0, len(time_logs) - 1, 2):
        day = time_logs[i].timestamp.weekday()
        if i + 1 < len(time_logs) and time_logs[i + 1].timestamp > time_logs[i].timestamp:
            work_duration = (time_logs[i + 1].timestamp - time_logs[i].timestamp).total_seconds() / 3600
            if day == 0:  # Monday
                work_hours_per_day['monday'] += work_duration
            elif day == 1:  # Tuesday
                work_hours_per_day['tuesday'] += work_duration
            elif day == 2:  # Wednesday
                work_hours_per_day['wednesday'] += work_duration
            elif day == 3:  # Thursday
                work_hours_per_day['thursday'] += work_duration
            elif day == 4:  # Friday
                work_hours_per_day['friday'] += work_duration
    if request.method == 'POST':
        form = ProgressReportForm(request.POST)
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
            # Insert the student details and other values into the PDF
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
            # Draw Virtual Conditions
            if form.cleaned_data['virtual_conditions'] == 'wfh':
                page.insert_text(coordinates['virtual_wfh'], '✓', fontsize=45, color=(0, 0, 0))
            elif form.cleaned_data['virtual_conditions'] == 'under':
                page.insert_text(coordinates['virtual_alternative'], '✓', fontsize=45, color=(0, 0, 0))
            # Fill other fields on the PDF
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
            # Insert the total work hours into the PDF
            total_work_hours = sum(work_hours_per_day.values())
            page.insert_text(coordinates['total_hours'], str(total_work_hours), fontsize=12, color=(0, 0, 0))
            buffer = BytesIO()
            pdf_document.save(buffer)
            pdf_document.close()
            buffer.seek(0)
            if not buffer.getvalue():
                messages.error(request, "PDF generation failed.")
                return redirect('students:progress-report')
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
                return redirect('students:progress-report')
    else:
        form = ProgressReportForm()
    return render(
        request, 
        'students/progress-report.html', 
        {
            'form': form,
            'firstName': firstName,
            'middleName': middleName,
            'lastName': lastName,
            'full_name': full_name,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
            'work_hours_per_day': work_hours_per_day,
            'current_date': current_date,
        }
    )

@login_required
def exportTimeLogToPDF(request):
    user = request.user
    if not hasattr(user, 'id'):
        return render(request, 'main/404.html', status=403)
    student = get_object_or_404(DataTableStudents, user=user)
    time_logs = TimeLog.objects.filter(
        student=student,
        timestamp__week_day__in=[1, 2, 3, 4, 5, 6, 7]
    ).order_by('timestamp')
    lunch_logs = LunchLog.objects.filter(student=student).order_by('timestamp')
    buffer = BytesIO()
    pdf_document = fitz.open(os.path.join(settings.PDF_ROOT, 'INTERNSHIP-TIMESHEET.pdf'))
    page = pdf_document[0]  
    y_positions = {
        'Monday': 100,
        'Tuesday': 120,
        'Wednesday': 140,
        'Thursday': 160,
        'Friday': 180
    }  
    total_hours_for_week = timedelta()
    last_time_in = None
    for log in time_logs:
        local_time = timezone.localtime(log.timestamp)
        time_formatted = local_time.strftime('%I:%M %p')
        date = log.timestamp.strftime('%Y-%m-%d')
        day_of_week = local_time.strftime('%A')    
        if log.action == 'IN':
            last_time_in = local_time
        elif log.action == 'OUT' and last_time_in:
            duration = local_time - last_time_in
            total_hours_for_week += duration
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            total_duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"        
            if day_of_week in y_positions:
                y_position = y_positions[day_of_week]               
                page.insert_text((105, y_position + + 225), date, fontsize=9, color=(0, 0, 0))
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
                y_positions[day_of_week] += 20
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
    page.insert_text((462, y_positions['Friday'] + 395), total_week_str, fontsize=12, color=(0, 0, 0))
    pdf_document.save(buffer)
    pdf_document.close()
    buffer.seek(0)  
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{fullname} - TimeSheet.pdf"'
    return response

@never_cache
@login_required
@csrf_exempt
def log_lunch(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    requirements_submitted = ApprovedDocument.objects.filter(student=student).exists()
    if not requirements_submitted:
        message = 'Please wait for the admin to approve your document before you can time in and time out.'
        return render(request, 'students/timeIn-timeOut.html', {
            'message': message,
            'forms': LunchLogForm(),
            'requirements_submitted': requirements_submitted,
        })
    if request.method == 'POST':
        forms = LunchLogForm(request.POST, request.FILES)
        if forms.is_valid():
            lunch_log = forms.save(commit=False)
            lunch_log.student = student
            lunch_log.timestamp = timezone.now()
            lunch_log.save()
            return redirect('students:clockin')
    return render(request, 'students/timeIn-timeOut.html', {'forms': LunchLogForm()})

@login_required
def ClockInAndOut(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    schedule_exists = Schedule.objects.filter(student=student).exists()
    requirements_submitted = ApprovedDocument.objects.filter(student=student).exists()
    notifications = Notification.objects.filter(student=student, is_read=False)
    unread_notifications_count = notifications.count()
    if not requirements_submitted:
        message = 'Please wait for the admin to approve your document before you can time in and time out.'
        return render(request, 'students/timeIn-timeOut.html', {
            'firstName': student.Firstname,
            'lastName': student.Lastname,
            'message': message,
            'form': TimeLogForm(),
            'schedule_exists': schedule_exists,
            'requirements_submitted': requirements_submitted,
            'notifications': notifications,
            'unread_notifications_count': unread_notifications_count,
        })
    if request.method == 'POST':
        form = TimeLogForm(request.POST, request.FILES)
        if form.is_valid():
            time_log = form.save(commit=False)
            time_log.student = student
            time_log.timestamp = timezone.now()
            time_log.save()
            # Redirect to refresh logs and also set last_action for the UI
            return redirect('students:clockin')
    # Get the last action (can be retrieved from the last time_log entry)
    last_action = TimeLog.objects.filter(student=student).order_by('-timestamp').first()
    last_action = last_action.action if last_action else None
    time_logs = TimeLog.objects.filter(student=student).order_by('timestamp')
    lunch_logs = LunchLog.objects.filter(student=student).order_by('timestamp')
    # Calculate total work time in seconds, considering both time logs and lunch breaks
    total_work_time_seconds = 0
    lunch_break_time_seconds = 0
    # Calculate total work hours from TimeLog entries
    for i in range(0, len(time_logs) - 1, 2):  # Iterate through time logs in pairs (Time In/Out)
        time_in = time_logs[i]
        if i + 1 < len(time_logs):
            time_out = time_logs[i + 1]
            if time_out.timestamp > time_in.timestamp:  # Ensure time out is after time in
                time_diff = (time_out.timestamp - time_in.timestamp).total_seconds()
                total_work_time_seconds += time_diff
    # Calculate lunch break time from LunchLog entries
    for i in range(0, len(lunch_logs) - 1, 2):  # Iterate through lunch logs in pairs (Lunch In/Out)
        lunch_in = lunch_logs[i]
        if i + 1 < len(lunch_logs):
            lunch_out = lunch_logs[i + 1]
            if lunch_out.timestamp > lunch_in.timestamp:  # Ensure lunch out is after lunch in
                lunch_diff = (lunch_out.timestamp - lunch_in.timestamp).total_seconds()
                lunch_break_time_seconds += lunch_diff
    # Adjust the total work time by subtracting the lunch break time
    adjusted_total_work_time_seconds = total_work_time_seconds - lunch_break_time_seconds
    # Convert adjusted total work time to hours and minutes
    total_work_hours, total_work_minutes = divmod(int(adjusted_total_work_time_seconds), 3600)
    total_work_minutes = (total_work_minutes // 60) % 60  # Correctly convert to minutes
    # Format the display string for total work time
    total_work_time_display = f"{total_work_hours} hours, {total_work_minutes} minutes"
    # Calculate required hours
    required_hours_seconds = student.get_required_hours() * 3600 if student.get_required_hours() is not None else 0
    remaining_hours_seconds = max(0, required_hours_seconds - adjusted_total_work_time_seconds)
    # Convert remaining time to hours and minutes
    remaining_hours, remaining_minutes = divmod(int(remaining_hours_seconds), 3600)
    remaining_minutes = (remaining_minutes // 60) % 60
    remaining_hours_display = f"{remaining_hours} hours, {remaining_minutes} minutes"
    paired_logs = []
    for i in range(0, len(time_logs), 2):
        if i + 1 < len(time_logs):
            paired_logs.append((time_logs[i], time_logs[i + 1]))
        else:
            paired_logs.append((time_logs[i], None))
    return render(request, 'students/timeIn-timeOut.html', {
        'required_hours_seconds': required_hours_seconds,
        'remaining_hours_seconds': remaining_hours_seconds,
        'total_work_time': total_work_time_display,
        'required_hours_time': f"{required_hours_seconds // 3600} hours",
        'remaining_hours_time': remaining_hours_display,
        'firstName': student.Firstname,
        'lastName': student.Lastname,
        'time_logs': paired_logs,
        'lunch_logs': lunch_logs,
        'current_time': timezone.localtime(timezone.now()),
        'form': TimeLogForm(),
        'lunch_form': LunchLogForm(),
        'schedule_exists': schedule_exists,
        'requirements_submitted': requirements_submitted,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'last_action': last_action,
        'message': message if not requirements_submitted else None,
    })

@never_cache
@login_required
@csrf_exempt
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
            return redirect('students:profile')
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

@never_cache
@login_required
@csrf_exempt
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
@csrf_exempt
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
@csrf_exempt
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
@csrf_exempt
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
                recipient_list = [pending_registration.PendingEmail]
                send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
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

@never_cache
@login_required
@csrf_exempt
def getTheRequirement(request):
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
    required_docs = [
        'Application Form', 'Parent Consent', 'Notice of Acceptance / MOA',
        'Endorsement Letter', 'Internship Contract Agreement', 'Medical Certificate',
        'Evaluation Form', 'Progress Report', 'Internship Time Sheet', 
        'Internship Exit Survey', 'Student Performance Evaluation',
        'Supporting Document of Time Sheet', 'Supporting Document of Progress Report'
    ]
    submitted_docs = TableSubmittedRequirement.objects.filter(
        student=student
    ).exclude(
        id__in=ApprovedDocument.objects.filter(student=student).values_list('id', flat=True)
    ).values_list('nameOfDocs', flat=True)

    submittedDoc = TableSubmittedRequirement.objects.filter(student=student).order_by('id')
    requirements = TableRequirements.objects.all().order_by('id')
    approved_docs = ApprovedDocument.objects.filter(student=student).values_list('nameOfDocs', flat=True)
    remaining_docs = [doc for doc in required_docs if doc not in submitted_docs and doc not in approved_docs]


    return render(request, 'students/requirements.html', {
        'form': form,
        'requirements': requirements,
        'remaining_docs': remaining_docs,
        'firstName': student.Firstname,
        'lastName': student.Lastname,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
        'unread_notifications_count': unread_notifications_count,
        'submittedDoc': submittedDoc
    })

@never_cache
@login_required
@csrf_exempt
def delete_submission(request, id):
    submission = get_object_or_404(TableSubmittedRequirement, id=id)
    if request.method == 'POST':
        submission.delete()
        return redirect('students:requirements')
    return render(request, 'students/requirements.html')
    
@never_cache
@login_required
@csrf_exempt
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

@never_cache
@csrf_exempt
def studentLogout(request) -> HttpResponseRedirect:
    logout(request)
    if 'is_student_logged_in' in request.session:
        del request.session['is_student_logged_in']
    return redirect('homepage:login-page')

@never_cache
@login_required
@csrf_exempt
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

@never_cache
@login_required
@csrf_exempt
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
