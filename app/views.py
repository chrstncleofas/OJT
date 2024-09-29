import re
import os
import json
from typing import Union
from django.urls import reverse
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from app.utils import saveActivityLogs
from .forms import CustomPasswordChangeForm
from app.forms import SetRenderingHoursForm
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from app.models import CustomUser, TableAnnouncement
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from students.forms import EditStudentForm, ScheduleSettingForm, GradeForm
from app.models import RenderingHoursTable, TableRequirements, TableContent
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse
from app.forms import EditProfileForm, AnnouncementForm, UploadRequirementForm, ContentForm, CustomUserCreationForm
from students.models import DataTableStudents, TimeLog, Schedule, TableSubmittedReport, TableSubmittedRequirement, PendingApplication, RejectApplication, Grade

HOME_URL_PATH = 'app/base.html'
DASHBOARD = 'app/dashboard.html'
MAIN_DASHBOARD = 'app/main-dashboard.html'
MANAGEMENT_STUDENT = 'app/manage-student.html'
ANNOUNCEMENT = 'app/announcement.html'
LIST_ANNOUNCEMENT = 'app/list-announcement.html'
PROFILE = 'app/profile.html'
CHANGE_PASSWORD = 'app/changePassword.html'

def home(request) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse]:        
    return render(request, HOME_URL_PATH)

def dashboard(request) -> HttpResponse:
    return render(request, DASHBOARD)

def mainDashboard(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    # Approve
    approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive').order_by('id')
    approve_count = approve.count()
    # Pending
    pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive').order_by('id')
    pending_count = pending.count()
    # Rejected
    reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive').order_by('id')
    reject_count = reject.count()

    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'approve_count': approve_count,
            'pending_count': pending_count,
            'reject_count': reject_count,
        })

    return render(
        request,
        MAIN_DASHBOARD,
        {
            'approve_count': approve_count,
            'pending_count': pending_count,
            'reject_count': reject_count,
            'firstName': firstName,
            'lastName': lastName
        }
    )

def studentManagement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)

    firstName = admin.first_name
    lastName = admin.last_name

    approved = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive').order_by('id')
    pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive').order_by('id')
    rejected = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive').order_by('id')
    archive = DataTableStudents.objects.filter(archivedStudents='Archive').order_by('id')

    active_tab = request.GET.get('tab', 'approved-students')
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 5))

    if active_tab == 'approved-students':
        students_list = approved
    elif active_tab == 'pending-application':
        students_list = pending
    elif active_tab == 'rejected-application':
        students_list = rejected
    elif active_tab == 'archive':
        students_list = archive
    else:
        students_list = []

    paginator = Paginator(students_list, per_page)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        'students': students,
        'pending': pending,
        'rejected': rejected,
        'archive': archive,
        'firstName': firstName,
        'lastName': lastName,
        'active_tab': active_tab,
        'per_page': per_page,
        'paginator': paginator,
    }

    return render(request, 'app/manage-student.html', context)

def profile(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=admin)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='UPDATE', request=request, description='Update admin/coordinator profile')
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = EditProfileForm(instance=admin)
    return render(request, PROFILE, {
        'form': form,
        'firstName': firstName,
        'lastName': lastName
    })

def changePass(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name   
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            saveActivityLogs(user=user, action='CHANGE', request=request, description='Changes password of admin/coordinator')
            messages.success(request, 'Your password was successfully updated!')
            return redirect('changePass')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    
    return render(request, CHANGE_PASSWORD, {
        'form': form,
        'firstName': firstName,
        'lastName': lastName
    })

def userLoginFunction(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_staff and not user.is_superuser:
                login(request, user)
                request.session['admin_password'] = user.password
                # Log the successful login action
                saveActivityLogs(user=user, action='LOGIN', request=request, description='Login admin/coordinator')
                return redirect('dashboard')
            else:
                messages.error(request, 'You do not have the necessary permissions to access this site.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'app/base.html')

@login_required
@require_POST
@csrf_exempt
def archivedStudent(request, id):
    user = request.user
    try:
        student = DataTableStudents.objects.get(pk=id)
        student.archivedStudents = 'Archive'
        student.save()
        saveActivityLogs(user=user, action='ARCHIVED', request=request, description='Archive students')
        return JsonResponse({'status': 'success', 'message': f'{student.Firstname} {student.Lastname} has been archived.'})
    except DataTableStudents.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def getAdminPasswordHash(request):
    return JsonResponse({'password': request.user.password})

@login_required
@require_POST
@csrf_exempt
def validateAdminPassword(request):
    input_password = json.loads(request.body).get('password')
    user = request.user

    if user.check_password(input_password):
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Incorrect password'})

def approveStudent(request, id):
    user = request.user

    pending_student = get_object_or_404(PendingApplication, id=id)

    new_user = CustomUser.objects.create(
        username=pending_student.PendingUsername,
        email=pending_student.PendingEmail,
        password=make_password(pending_student.PendingPassword),
        first_name=pending_student.PendingFirstname,
        last_name=pending_student.PendingLastname,
    )
    
    new_user.save()

    new_student = DataTableStudents.objects.create(
        user=new_user,
        StudentID=pending_student.PendingStudentID,
        Firstname=pending_student.PendingFirstname,
        Middlename=pending_student.PendingMiddlename,
        Lastname=pending_student.PendingLastname,
        Email=pending_student.PendingEmail,
        Address=pending_student.PendingAddress,
        Number=pending_student.PendingNumber,
        Course=pending_student.PendingCourse,
        Year=pending_student.PendingYear,
        Username=pending_student.PendingUsername,
        Password=new_user.password,
        status='Approved',
        archivedStudents='NotArchive',
    )
    
    new_student.save()

    pending_student.delete()

    saveActivityLogs(user=user, action='APPROVED', request=request, description=f"Approved student {new_student.Firstname} {new_student.Lastname}")

    subject = 'Your OJT Management System Account Has Been Approved'
    message = render_to_string('app/approval_email.txt', {
        'first_name': new_student.Firstname,
        'last_name': new_student.Lastname,
    })
    recipient_list = [new_student.Email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
    
    messages.success(request, f"{new_student.Firstname} {new_student.Lastname} has been approved and added to the student list.")

    return redirect('studentManagement')

@csrf_exempt
def rejectStudent(request, id):
    user = request.user
    if request.method == 'POST':
        try:
            try:
                pending_application = PendingApplication.objects.get(id=id)
            except PendingApplication.DoesNotExist:
                return JsonResponse({'status': 'success', 'message': 'Pending application was already deleted.'})

            data = json.loads(request.body)
            reason = data.get('reason', 'No reason provided')

            rejected = RejectApplication.objects.create(
                RejectStudentID=pending_application.PendingStudentID,
                RejectFirstname=pending_application.PendingFirstname,
                RejectMiddlename=pending_application.PendingMiddlename,
                RejectLastname=pending_application.PendingLastname,
                RejectPrefix=pending_application.PendingPrefix,
                RejectEmail=pending_application.PendingEmail,
                RejectAddress=pending_application.PendingAddress,
                RejectNumber=pending_application.PendingNumber,
                RejectCourse=pending_application.PendingCourse,
                RejectYear=pending_application.PendingYear,
                RejectUsername=pending_application.PendingUsername,
                RejectPassword=make_password(pending_application.PendingPassword),
                RejectStatus='RejectedApplication'
            )

            rejected.save()

            saveActivityLogs(user=user, action='REJECTED', request=request, description='Rejected pending student application')

            subject = 'Account Rejected'
            message = render_to_string('app/rejection_email.txt', {
                'first_name': pending_application.PendingFirstname,
                'last_name': pending_application.PendingLastname,
                'reason': reason
            })
            recipient_list = [pending_application.PendingEmail]
            send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)

            pending_application.delete()

            return JsonResponse({'status': 'success', 'message': 'Student successfully rejected.'})

        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)

    return redirect('studentManagement')

def unArchivedStudent(request, id):
    user = request.user
    student = DataTableStudents.objects.get(id=id)
    student.archivedStudents = 'UnArchive'
    student.save()
    saveActivityLogs(user=user, action='UNARCHIVED', request=request, description='Unarchive students')
    messages.success(request, f'{student.Firstname} {student.Lastname} has been remove to archived.')
    return redirect(reverse('studentManagement'))

def logoutView(request) -> HttpResponseRedirect:
    user = request.user
    if user.is_authenticated:
        saveActivityLogs(
            user=user,
            action='LOGOUT',
            request=request,
            description='Logout page'
        )
    logout(request)
    return redirect(home)

def isAdmin(user):
    user_admin = user.is_superuser
    user_staff = user.is_staff
    return user_admin or user_staff

def viewPendingApplication(request, id):
    user = request.user
    try:
        students = PendingApplication.objects.get(id=id)
    except PendingApplication.DoesNotExist:
        return redirect('studentManagement')

    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    return render(
        request,
        'app/pending-view-page.html',
        {
            'students': students,
            'firstName': firstName,
            'lastName': lastName
        }
    )

def clean_filename(filename):
    """Remove timestamp from the filename."""
    if filename:
        return re.sub(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_', '', filename)
    return filename

def submittedRequirementOfStudents(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    student = get_object_or_404(DataTableStudents, id=id)
    firstName = admin.first_name
    lastName = admin.last_name

    studentFirstname = student.Firstname
    studentLastname = student.Lastname

    progress_reports = TableSubmittedReport.objects.filter(student=student).order_by('-date_submitted', 'id')
    requirements = TableSubmittedRequirement.objects.filter(student=student).order_by('-submission_date', 'id')
    cleaned_reports = [(report, clean_filename(report.report_file.name)) for report in progress_reports]

    context = {
        'firstName': firstName,
        'lastName': lastName,
        'studentFirstname': studentFirstname,
        'studentLastname': studentLastname,
        'cleaned_reports': cleaned_reports,
        'requirements': requirements,
    }

    return render(request, 'app/view-submitted-requirement.html', context)

def getTheSubmitRequirements(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    search_query = request.GET.get('search', '')

    students = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive').order_by('id')

    if search_query:
        students = students.filter(
            Q(Firstname__icontains=search_query)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/grading.html', {'listOfStudents': students})
    
    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(students, per_page)

    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    return render(request, 'app/list-submission-student.html', {
        'listOfStudents': students,
        'firstName': firstName,
        'lastName': lastName
    })



def studentInformation(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    student = get_object_or_404(DataTableStudents, id=id)
    firstName = admin.first_name
    lastName = admin.last_name

    studentFirstname = student.Firstname
    studentLastname = student.Lastname

    selected_student = get_object_or_404(DataTableStudents, id=id)
    time_logs = TimeLog.objects.filter(student=selected_student).order_by('timestamp')
    
    total_work_seconds = 0
    daily_total = timedelta()
    paired_logs = []
    eight_hours = timedelta(hours=9)
    
    i = 0
    
    while i < len(time_logs):
        if time_logs[i].action == 'IN':
            if i + 1 < len(time_logs) and time_logs[i + 1].action == 'OUT':
                paired_logs.append((time_logs[i], time_logs[i + 1]))
                work_period = time_logs[i + 1].timestamp - time_logs[i].timestamp
                work_period = eight_hours
                if work_period > timedelta(hours=1):
                    work_period -= timedelta(hours=1)
                    
                daily_total += work_period
                i += 1
        i += 1
    
    total_work_seconds = daily_total.total_seconds()
    required_hours_seconds = student.get_required_hours() * 3600 if student.get_required_hours() is not None else 0
    remaining_hours_seconds = required_hours_seconds - total_work_seconds
    if request.method == 'POST':
        total_work_time_input = request.POST.get('total_work_time')
        required_hours_time_input = request.POST.get('required_hours_time')
        remaining_hours_time_input = request.POST.get('remaining_hours_time')
        total_work_seconds = convert_time_to_seconds(total_work_time_input)
        required_hours_seconds = convert_time_to_seconds(required_hours_time_input)
        remaining_hours_seconds = convert_time_to_seconds(remaining_hours_time_input)
        
    full_schedule = Schedule.objects.filter(student=student, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('id')
    grades = Grade.objects.filter(student=student).order_by('id')
    progress_reports = TableSubmittedReport.objects.filter(student=selected_student).order_by('-date_submitted', 'id')
    requirements = TableSubmittedRequirement.objects.filter(student=selected_student).order_by('-submission_date', 'id')

    cleaned_reports = [(report, clean_filename(report.report_file.name)) for report in progress_reports]

    def format_seconds(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

    context = {
        'paired_logs': paired_logs,
        'total_work_seconds': total_work_seconds,
        'required_hours_seconds': required_hours_seconds,
        'remaining_hours_seconds': remaining_hours_seconds,
        'total_work_time': format_seconds(total_work_seconds),
        'required_hours_time': format_seconds(required_hours_seconds),
        'remaining_hours_time': format_seconds(remaining_hours_seconds),
        'firstName': firstName,
        'lastName': lastName,
        'studentFirstname': studentFirstname,
        'studentLastname': studentLastname,
        'full_schedule': full_schedule,
        'cleaned_reports': cleaned_reports,
        'requirements': requirements,
        'grades': grades
    }
    return render(request, 'app/TimeLogs.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.is_staff = True
            new_user.save()
            messages.success(request, "Admin user successfully registered.")
            return redirect('register')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(
        request, 'app/register.html', 
        {
            'form': form,
        }
    )

def convert_time_to_seconds(time_str):
    """Convert a time string like '1 hours, 30 minutes' to total seconds."""
    time_parts = time_str.split(',')
    total_seconds = 0
    for part in time_parts:
        if 'hour' in part:
            hours = int(part.split()[0])
            total_seconds += hours * 3600
        elif 'minute' in part:
            minutes = int(part.split()[0])
            total_seconds += minutes * 60
    return total_seconds

@login_required
def set_rendering_hours(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    if request.method == 'POST':
        form = SetRenderingHoursForm(request.POST)
        upload_form = UploadRequirementForm(request.POST, request.FILES)
        if form.is_valid():
            bsit_hours = form.cleaned_data.get('bsit_hours')
            bscs_hours = form.cleaned_data.get('bscs_hours')
            RenderingHoursTable.objects.update_or_create(
                course='BS Information Technology',
                defaults={'required_hours': bsit_hours}
            )
            RenderingHoursTable.objects.update_or_create(
                course='BS Computer Science',
                defaults={'required_hours': bscs_hours}
            )
            saveActivityLogs(user=user, action='SET', request=request, description='Set render time')
            return redirect('set_rendering_hours')
        
        elif upload_form.is_valid():
            requirement = upload_form.save(commit=False)
            requirement.save()
            # Log activity for file upload
            saveActivityLogs(user=user, action='UPLOAD', request=request, description='Uploaded new requirement')
            return redirect('set_rendering_hours')
    else:
        try:
            bsit_hours = RenderingHoursTable.objects.get(course='BS Information Technology').required_hours
        except RenderingHoursTable.DoesNotExist:
            bsit_hours = None

        try:
            bscs_hours = RenderingHoursTable.objects.get(course='BS Computer Science').required_hours
        except RenderingHoursTable.DoesNotExist:
            bscs_hours = None

        form = SetRenderingHoursForm(initial={
            'bsit_hours': bsit_hours,
            'bscs_hours': bscs_hours,
        })

        upload_form = UploadRequirementForm()

    # Get all uploaded requirements
    requirements = TableRequirements.objects.all()
    return render(request, 'app/settings.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName,
        'requirements': requirements,
        'upload_form': upload_form
    })

def editRenderHours(request):
    user = request.user
    if request.method == 'POST':
        form = SetRenderingHoursForm(request.POST)
        if form.is_valid():
            bsit_hours = form.cleaned_data.get('bsit_hours')
            bscs_hours = form.cleaned_data.get('bscs_hours')
            RenderingHoursTable.objects.update_or_create(
                course='BS Information Technology',
                defaults={'required_hours': bsit_hours}
            )
            RenderingHoursTable.objects.update_or_create(
                course='BS Computer Science',
                defaults={'required_hours': bscs_hours}
            )
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit render time')
            return redirect('set_rendering_hours')
    else:
        form = SetRenderingHoursForm()

    return render(request, 'app/settings.html', {
        'form': form,
    })

def listOfAnnouncement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    search_query = request.GET.get('search', '')

    announcements = TableAnnouncement.objects.all().order_by('id')

    if search_query:
        announcements = announcements.filter(
            Q(Title__icontains=search_query)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, LIST_ANNOUNCEMENT, {'listOfAnnouncement': announcements})

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(announcements, per_page)

    try:
        announcements = paginator.page(page)
    except PageNotAnInteger:
        announcements = paginator.page(1)
    except EmptyPage:
        announcements = paginator.page(paginator.num_pages)

    return render(request, LIST_ANNOUNCEMENT, {
        'listOfAnnouncement': announcements,
        'firstName': firstName,
        'lastName': lastName
    })

def listOfContent(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    search_query = request.GET.get('search', '')

    content = TableContent.objects.all().order_by('id')

    if search_query:
        content = content.filter(
            Q(nameOfContent__icontains=search_query)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/allContentPage.html', {'listOfContent': content})

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(content, per_page)

    try:
        content = paginator.page(page)
    except PageNotAnInteger:
        content = paginator.page(1)
    except EmptyPage:
        content = paginator.page(paginator.num_pages)

    return render(request, 'app/allContentPage.html', {
        'listOfContent': content,
        'firstName': firstName,
        'lastName': lastName
    })

def postAnnouncement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='POST', request=request, description='Post announcement')
            return redirect('listOfAnnouncement')
    else:
        form = AnnouncementForm()
    return render(request, ANNOUNCEMENT,
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName
        }
    )

def postContent(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='POST', request=request, description='Post content')
            return redirect('content')
    else:
        form = ContentForm()
    return render(request, 'app/addContentForm.html',
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName
        }
    )

def editAnnouncement(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    announcement = get_object_or_404(TableAnnouncement, id=id)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit announcement')
            return redirect('listOfAnnouncement')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'app/edit-announcement.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName,
        'announcement': announcement,
    })

def editContent(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    content = get_object_or_404(TableContent, id=id)

    if request.method == 'POST':
        form = ContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit content')
            return redirect('all-content')
    else:
        form = ContentForm(instance=content)

    return render(request, 'app/edit-content.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName,
        'content': content,
    })

def deleteAnnouncement(request, id):
    user = request.user
    announcement = get_object_or_404(TableAnnouncement, id=id)
    if request.method == 'POST':
        announcement.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete announcement')
        return redirect('listOfAnnouncement')
    return render(request, LIST_ANNOUNCEMENT, {'announcement': announcement})

def deleteContent(request, id):
    user = request.user
    content = get_object_or_404(TableContent, id=id)
    if request.method == 'POST':
        content.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete content')
        return redirect('all-content')
    return render(request, 'app/allContentPage.html', {'content': content})

def deleteRequirementDocuments(request, id):
    user = request.user
    docs = get_object_or_404(TableRequirements, id=id)
    if request.method == 'POST':
        docs.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete documents')
        return redirect('set_rendering_hours')
    return render(request, 'app/settings.html', {'docs': docs})

def setSchedule(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    student = get_object_or_404(DataTableStudents, id=id)
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
            saveActivityLogs(user=user, action='SET', request=request, description='Set schedule')
            return redirect('editStudentDetails', id=id)
    else:
        form = ScheduleSettingForm()

    return render(request, 'app/set-schedule.html', {
        'form': form,
        'student': student,
        'firstName': firstName,
        'lastName': lastName,
    })

def editStudentDetails(request, id):
    user = request.user
    student = get_object_or_404(DataTableStudents, pk=id)
    # 
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    # 
    if request.method == 'POST':
        form = EditStudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit students details')
            messages.success(request, 'Student details updated successfully.')
            return redirect('studentManagement')
    else:
        form = EditStudentForm(instance=student)

    return render(request, 'app/edit-student.html', {
        'form': form,
        'student': student,
        'firstName': firstName,
        'lastName': lastName,
    })

def getAllStudentsForGrading(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    search_query = request.GET.get('search', '')
    searchgrade= request.GET.get('search-items', '')

    students = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive').order_by('id')
    withGrade = Grade.objects.all().order_by('id')

    if search_query:
        students = students.filter(
            Q(Firstname__icontains=search_query)
        )
    
    name_parts = searchgrade.split()
    if len(name_parts) == 2:
        withGrade = withGrade.filter(
            Q(student__Firstname__icontains=name_parts[0]) &
            Q(student__Lastname__icontains=name_parts[1])
        )
    else:
        withGrade = withGrade.filter(
            Q(student__Firstname__icontains=searchgrade) |
            Q(student__Lastname__icontains=searchgrade)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/grading.html', {'listOfStudents': students})
    
    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(students, per_page)

    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    return render(request, 'app/grading.html', {
        'listOfStudents': students,
        'withGrade': withGrade,
        'firstName': firstName,
        'lastName': lastName
    })

def gradeFormula(evaluation, docs, oral_interview):
    eval_score = (evaluation / 30 * 50 + 50) * 0.60
    docs_score = (docs / 40 * 50 + 50) * 0.30
    oral_score = (oral_interview / 30 * 50 + 50) * 0.10
    final_grade = eval_score + docs_score + oral_score
    return round(final_grade, 1)

def gradeCalculator(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    final_grade = None
    status = None

    student = get_object_or_404(DataTableStudents, id=id)
    gradesResult = Grade.objects.filter(student=student)
    
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.student = student

            final_grade = gradeFormula(
                form.cleaned_data['evaluation'], 
                form.cleaned_data['docs'], 
                form.cleaned_data['oral_interview']
            )
            grade.final_grade = final_grade

            grade.status = 'Passed' if final_grade > 74 else 'Failed'
            grade.save()

            return render(request, 'app/computeGradePage.html', {
                'form': form,
                'student': student,
                'final_grade': final_grade,
                'status': status,
                'gradesResult': gradesResult
            })
    else:
        form = GradeForm()

    return render(
        request,
        'app/computeGradePage.html',
        {
            'form': form,
            'final_grade': final_grade,
            'student': student,
            'status' : status,
            'firstName': firstName,
            'lastName': lastName,
            'gradesResult': gradesResult
        }
    )

def getAnnouncementNotLogin(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'app/getAnnouncementNotLogin.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

def getAnnouncement(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'app/getAnnouncementLogin.html', 
        {
            'announcements': enabledAnnouncement
        }
    )
