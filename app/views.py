import json
from typing import Union
from datetime import timedelta
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from app.utils import saveActivityLogs
from app.models import RenderingHoursTable
from .forms import CustomPasswordChangeForm
from app.forms import SetRenderingHoursForm
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from app.models import CustomUser, TableAnnouncement
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from app.forms import EditProfileForm, AnnouncementForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from students.forms import EditStudentForm, ScheduleSettingForm
from students.models import DataTableStudents, TimeLog, Schedule
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse

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
    approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive')
    approve_count = approve.count()
    # Pending
    pending = DataTableStudents.objects.filter(status='Pending')
    pending_count = pending.count()
    # Rejected
    reject = DataTableStudents.objects.filter(status='Rejected')
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

def studentManagement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    # 
    firstName = admin.first_name
    lastName = admin.last_name
    # 
    approved = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive')
    # 
    pending = DataTableStudents.objects.filter(status='Pending')
    # 
    rejected = DataTableStudents.objects.filter(status='Rejected')
    # 
    archive = DataTableStudents.objects.filter(archivedStudents='Archive')

    active_tab = request.GET.get('tab', 'approved-students')  # Default to 'approved-students' tab
    return render(
        request,
        MANAGEMENT_STUDENT,
        {
            'getListOfApproveStudent': approved,
            'getAllPendingRegister': pending,
            'getAllRejectedApplication': rejected,
            'getListOfArchivedStudents': archive,
            'firstName': firstName,
            'lastName': lastName,
            'active_tab': active_tab,
        }
    )

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
    student = DataTableStudents.objects.get(id=id)
    student.status = 'Approved'
    student.save()
    saveActivityLogs(user=user, action='APPROVED', request=request, description='Approve students')
    subject = 'Your OJT Management System Account Has Been Approved'
    message = render_to_string('app/approval_email.txt', {
        'first_name': student.Firstname,
        'last_name': student.Lastname,
    })
    recipient_list = [student.Email]
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
    return redirect(reverse('studentManagement'))

@csrf_exempt
def rejectStudent(request, id):
    user = request.user
    if request.method == 'POST':
        student = DataTableStudents.objects.get(id=id)
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        student.status = 'Rejected'
        student.save()
        saveActivityLogs(user=user, action='REJECTED', request=request, description='Rejected students')
        subject = 'Account Rejected'
        message = render_to_string('app/rejection_email.txt', {
            'first_name': student.Firstname,
            'last_name': student.Lastname,
            'reason': reason
        })
        recipient_list = [student.Email]
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

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
    logout(request)
    saveActivityLogs(
        user=user,
        action='LOGOUT',
        request=request,
        description='Logout page'
    )
    return redirect(home)

def isAdmin(user):
    user_admin = user.is_superuser
    user_staff = user.is_staff
    return user_admin or user_staff

@user_passes_test(isAdmin)
def timeSheet(request):
    students = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive')
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    return render(
        request,
        'app/timeSheet.html',
        {
            'students': students,
            'firstName': firstName,
            'lastName': lastName
        }
    )

def viewPendingApplication(request, id):
    students = get_object_or_404(DataTableStudents, id=id)
    user = request.user
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


def viewTimeLogs(request, student_id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    student = get_object_or_404(DataTableStudents, id=student_id)
    firstName = admin.first_name
    lastName = admin.last_name

    studentFirstname = student.Firstname
    studentLastname = student.Lastname

    selected_student = get_object_or_404(DataTableStudents, id=student_id)
    time_logs = TimeLog.objects.filter(student=selected_student).order_by('timestamp')
    total_work_seconds = 0
    daily_total = timedelta()
    paired_logs = []
    i = 0
    while i < len(time_logs):
        if time_logs[i].action == 'IN':
            if i + 1 < len(time_logs) and time_logs[i + 1].action == 'OUT':
                paired_logs.append((time_logs[i], time_logs[i + 1]))
                work_period = time_logs[i + 1].timestamp - time_logs[i].timestamp
                if work_period > timedelta(hours=1):
                    work_period -= timedelta(hours=1)
                daily_total += work_period
                i += 1
        i += 1
    total_work_seconds = daily_total.total_seconds()
    required_hours_seconds = student.get_required_hours() * 3600 if student.get_required_hours() is not None else 0
    remaining_hours_seconds = required_hours_seconds - total_work_seconds
    full_schedule = Schedule.objects.filter(student=student, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('id')

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
    }
    return render(request, 'app/TimeLogs.html', context)

def viewStudentInformation(request, student_id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    try:
        student = DataTableStudents.objects.get(pk=student_id)
    except DataTableStudents.DoesNotExist:
        return HttpResponse('Student not found', status=404)
    return render(
        request, 'app/student-view-page.html', 
        {
            'student': student,
            'firstName': firstName,
            'lastName': lastName
        }
    )

@login_required
def set_rendering_hours(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

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
            saveActivityLogs(user=user, action='SET', request=request, description='Set render time')
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

    return render(request, 'app/settings.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName
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

    announcements = TableAnnouncement.objects.all()

    if search_query:
        listOfAnnouncementInTheTable = listOfAnnouncementInTheTable.filter(
            Q(Title__icontains=search_query)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, LIST_ANNOUNCEMENT, {'listOfAnnouncement': listOfAnnouncementInTheTable})
    
    return render(request, LIST_ANNOUNCEMENT, {
        'listOfAnnouncement': announcements,
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

def deleteAnnouncement(request, id):
    user = request.user
    announcement = get_object_or_404(TableAnnouncement, id=id)
    if request.method == 'POST':
        announcement.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete announcement')
        messages.success(request, 'Announcement has been deleted successfully.')
        return redirect('listOfAnnouncement')
    return render(request, LIST_ANNOUNCEMENT, {'announcement': announcement})

def setSchedule(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    student = get_object_or_404(DataTableStudents, id=id)
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
