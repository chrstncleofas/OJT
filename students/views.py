import os
import fitz
from io import BytesIO
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from app.models import TableAnnouncement
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils.timezone import now, localtime
from django.template.loader import render_to_string
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from students.models import DataTableStudents, TimeLog, Schedule
from students.forms import StudentRegistrationForm, UserForm, ChangePasswordForm, TimeLogForm, StudentProfileForm, ScheduleSettingForm, FillUpPDFForm

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

def getAnnouncement(request):
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
    rect = fitz.Rect(x, y, x + max_width, y + 1000)  # Set a reasonable height to fit long text
    page.insert_textbox(rect, text, fontsize=fontsize, fontname=fontname, align=0)


def progressReport(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)
    firstName = student.Firstname
    lastName = student.Lastname

    if request.method == 'POST':
        form = FillUpPDFForm(request.POST)
        if form.is_valid():
            pdf_path = os.path.join(settings.PDF_ROOT, 'PROGRESS-REPORT.pdf')
            pdf_document = fitz.open(pdf_path)
            # Use the first page; adjust as needed for multiple pages
            page = pdf_document[0]
            
            # Coordinates for each field (adjust these as needed)
            coordinates = {
                'name_field': (170, 157),
                'classification_local': (200, 195),
                'classification_international': (330, 195),
                'classification_in_campus': (220, 210),
                'classification_off_campus': (226, 225),
                'modality_actual': (200, 239),
                'modality_virtual': (330, 239),
                'virtual_wfh': (350, 255),
                'virtual_alternative': (350, 270),
                'hte_name': (170, 260),
                'hte_address': (170, 275),
                'department_division': (250, 290),
            }

            # Draw text fields
            page.insert_text(coordinates['name_field'], form.cleaned_data['student_name'], fontsize=12, color=(0, 0, 0))
            # Draw Internship Classification
            if form.cleaned_data['internship_classification'] == 'local':
                page.insert_text(coordinates['classification_local'], '✓', fontsize=75, color=(0, 0, 0))
            elif form.cleaned_data['internship_classification'] == 'international':
                page.insert_text(coordinates['classification_international'], '✓', fontsize=75, color=(0, 0, 0))
            # Draw Local Condition
            if form.cleaned_data['local_condition'] == 'inCampus':
                page.insert_text(coordinates['classification_in_campus'], '✓', fontsize=75, color=(0, 0, 0))
            elif form.cleaned_data['local_condition'] == 'offCampus':
                page.insert_text(coordinates['classification_off_campus'], '✓', fontsize=75, color=(0, 0, 0))
            # Draw Modality
            if form.cleaned_data['internship_modality'] == 'actual':
                page.insert_text(coordinates['modality_actual'], '✓', fontsize=75, color=(0, 0, 0))
            elif form.cleaned_data['internship_modality'] == 'virtual':
                page.insert_text(coordinates['modality_virtual'], '✓', fontsize=75, color=(0, 0, 0))
            # Draw Virtual
            if form.cleaned_data['virtual_conditions'] == 'wfh':
                page.insert_text(coordinates['virtual_wfh'], '✓', fontsize=75, color=(0, 0, 0))
            elif form.cleaned_data['virtual_conditions'] == 'under':
                page.insert_text(coordinates['virtual_alternative'], '✓', fontsize=75, color=(0, 0, 0))
            # Draw 
            page.insert_text(coordinates['hte_name'], form.cleaned_data['hte_name'], fontsize=12, color=(0, 0, 0))
            page.insert_text(coordinates['hte_address'], form.cleaned_data['hte_address'], fontsize=12, color=(0, 0, 0))
            page.insert_text(coordinates['department_division'], form.cleaned_data['department_division'], fontsize=12, color=(0, 0, 0))

            # Font size for text
            text_fontsize = 9

            # Draw daily progress
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            y_start = 350  # Starting y-coordinate for progress entries
            description_max_width = 265  # Maximum width for text wrapping

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
                
                y_start += 60
            
            # Save the modified PDF to a buffer
            buffer = BytesIO()
            pdf_document.save(buffer)
            pdf_document.close()
            buffer.seek(0)
            return HttpResponse(buffer, content_type='application/pdf')
    else:
        form = FillUpPDFForm()
    
    return render(
        request, 
        'students/progress-report.html', 
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName,
        }
    )
    
def TimeInAndTimeOut(request):
    user = request.user
    student = get_object_or_404(DataTableStudents, user=user)

    if request.method == 'POST':
        form = TimeLogForm(request.POST, request.FILES)
        if request.method == 'POST':
            form = TimeLogForm(request.POST, request.FILES)
            if form.is_valid():
                time_log = form.save(commit=False)
                time_log.student = student
                time_log.timestamp = timezone.now()
                time_log.save()
                return redirect('students:TimeInAndTimeOut')
    else:
        form = TimeLogForm()

    current_time = localtime(now())

    firstName = student.Firstname
    lastName = student.Lastname
    # Determine last action for button logic
    time_logs = TimeLog.objects.filter(student=student).order_by('-timestamp')
    last_action = time_logs[0].action if time_logs else ''
    full_schedule = Schedule.objects.filter(student=student, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('id')

    return render(
        request,
        'students/timeIn-timeOut.html',
        {
            'firstName': firstName,
            'lastName': lastName,
            'time_logs': time_logs,
            'current_time': current_time,
            'form': form,
            'full_schedule': full_schedule,
            'last_action': last_action,
        }
    )

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
            return redirect('students:register')
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
