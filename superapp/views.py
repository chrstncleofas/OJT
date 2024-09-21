import re
from typing import Union
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.core.mail import send_mail
from app.utils import saveActivityLogs
from superapp.forms import EditUsersForm
from app.models import RenderingHoursTable
from app.forms import SetRenderingHoursForm
from app.forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from app.models import CustomUser, StoreActivityLogs
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from students.models import DataTableStudents, TimeLog, Schedule
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from app.models import TableAnnouncement, StoreActivityLogs, TableRequirements, TableContent
from app.forms import EditUsersDetailsForm, AnnouncementForm, UploadRequirementForm, ContentForm
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse
from students.models import PendingApplication, RejectApplication, Grade, TableSubmittedRequirement, TableSubmittedReport

DASHBOARD = 'superapp/dashboard.html'
MAIN_DASHBOARD = 'superapp/main-dashboard.html'
HOME_URL_PATH = 'superapp/base.html'
MANAGEMENT_STUDENT = 'superapp/manage-student.html'
LIST_ANNOUNCEMENT = 'superapp/announcement.html'
POST_ANNOUNCEMENT_PAGE = 'superapp/add-announcement.html'

def superHome(request) -> Union[HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse]:        
    return render(request, HOME_URL_PATH)

def superAdminDashboard(request) -> HttpResponse:
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
    pending = PendingApplication.objects.filter(StatusApplication='PendingApplication')
    pending_count = pending.count()
    # Rejected
    reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication')
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

def superAdminLogin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_superuser:
                login(request, user)
                saveActivityLogs(user=user, action='LOGIN', request=request, description='Login Super Admin')
                return redirect('superapp:superAdminDashboard')
            else:
                messages.error(request, 'You do not have the necessary permissions to access this site.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'superapp/base.html')

def loggingOut(request) -> HttpResponseRedirect:
    user = request.user
    logout(request)
    if user.is_authenticated:
        saveActivityLogs(
            user=user,
            action='LOGOUT',
            request=request,
            description='Logout Super Admin'
        )
    return redirect('superapp:superHome')

def studentManagement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    
    firstName = admin.first_name
    lastName = admin.last_name
    
    approved = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive')
    pending = PendingApplication.objects.filter(StatusApplication='PendingApplication')
    rejected = RejectApplication.objects.filter(RejectStatus='RejectedApplication')
    archive = DataTableStudents.objects.filter(archivedStudents='Archive')
    
    active_tab = request.GET.get('tab', 'approved-students')
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))

    if active_tab == 'approved-students':
        students_list = approved
    elif active_tab == 'pending-application':
        students_list = pending
    elif active_tab == 'rejected-application':
        students_list = rejected
    else:  # Archive tab
        students_list = archive

    paginator = Paginator(students_list, per_page)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)
    
    for student in approved:
        last_login = student.user.last_login
        if last_login:
            local_last_login = timezone.localtime(last_login)
            last_login_formatted = local_last_login.strftime('%b. %d, %Y, %I:%M %p')
        else:
            last_login_formatted = 'No login recorded'
        
        student.last_login_formatted = last_login_formatted
    
    return render(
        request,
        MANAGEMENT_STUDENT,
        {
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
    )

def clean_filename(filename):
    """Remove timestamp from the filename."""
    if filename:
        return re.sub(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_', '', filename)
    return filename

def viewStudent(request, id):
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
    return render(request, 'superapp/TimeLogs.html', context)

def getAllTheUserAccount(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)    
    firstName = admin.first_name
    lastName = admin.last_name
    # 
    search_query = request.GET.get('search', '')
    # 
    admin_users = CustomUser.objects.filter(Q(is_staff=True) or Q(is_superuser=True))
    # 
    if search_query:
        admin_users = admin_users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Pagination logic
    page = request.GET.get('page', 1)  # Get the current page number from the request
    per_page = request.GET.get('per_page', 5)  # Default items per page is set to 5

    paginator = Paginator(admin_users, per_page)  # Create paginator object

    try:
        admin_users = paginator.page(page)  # Get the current page of results
    except PageNotAnInteger:
        admin_users = paginator.page(1)  # If page is not an integer, deliver first page
    except EmptyPage:
        admin_users = paginator.page(paginator.num_pages)  

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'superapp/users.html', {'getAllTheUserAccount': admin_users})
    # 
    return render(request, 'superapp/users.html', {
        'getAllTheUserAccount': admin_users,
        'firstName': firstName,
        'lastName': lastName
    })

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

def getActivityLogs(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)

    firstName = admin.first_name
    lastName = admin.last_name

    search_query = request.GET.get('search', '')

    admin_users = StoreActivityLogs.objects.all().order_by('-timestamp', 'id')

    if search_query:
        admin_users = admin_users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(position__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(admin_users, per_page)
    try:
        admin_users = paginator.page(page)
    except PageNotAnInteger:
        admin_users = paginator.page(1)
    except EmptyPage:
        admin_users = paginator.page(paginator.num_pages)

    # Limit pagination range to 5 pages at a time
    max_display_pages = 5
    current_page = admin_users.number
    total_pages = paginator.num_pages

    # Determine start and end of the pagination range
    start_page = max(current_page - 2, 1)
    end_page = min(start_page + max_display_pages - 1, total_pages)

    if end_page - start_page < max_display_pages:
        start_page = max(end_page - max_display_pages + 1, 1)

    pagination_range = range(start_page, end_page + 1)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'superapp/activitylogs.html', {'getActivityLogs': admin_users})

    return render(request, 'superapp/activitylogs.html', {
        'getActivityLogs': admin_users,
        'firstName': firstName,
        'lastName': lastName,
        'per_page': per_page,
        'pagination_range': pagination_range,
        'total_pages': total_pages
    })

def getAllTheListAnnouncement(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    
    search_query = request.GET.get('search', '')
    
    listOfAnnouncementInTheTable = TableAnnouncement.objects.all().order_by('id')
    
    if search_query:
        listOfAnnouncementInTheTable = listOfAnnouncementInTheTable.filter(
            Q(Title__icontains=search_query)
        )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'superapp/announcement.html', {'getAllTheListAnnouncement': listOfAnnouncementInTheTable})
    
    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(listOfAnnouncementInTheTable, per_page)

    try:
        listOfAnnouncementInTheTable = paginator.page(page)
    except PageNotAnInteger:
        listOfAnnouncementInTheTable = paginator.page(1)
    except EmptyPage:
        listOfAnnouncementInTheTable = paginator.page(paginator.num_pages)
    
    return render(request, 'superapp/announcement.html', {
        'getAllTheListAnnouncement': listOfAnnouncementInTheTable,
        'firstName': firstName,
        'lastName': lastName,
        'per_page': per_page,
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
    return render(request, POST_ANNOUNCEMENT_PAGE,
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
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit announcement details')
            return redirect('superapp:getAllTheListAnnouncement')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'superapp/edit-announcement.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName,
        'announcement': announcement,
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
        return render(request, 'superapp/allContentPage.html', {'listOfContent': content})

    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 5)

    paginator = Paginator(content, per_page)

    try:
        content = paginator.page(page)
    except PageNotAnInteger:
        content = paginator.page(1)
    except EmptyPage:
        content = paginator.page(paginator.num_pages)

    return render(request, 'superapp/allContentPage.html', {
        'listOfContent': content,
        'firstName': firstName,
        'lastName': lastName
    })

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
            return redirect('superapp:content')
    else:
        form = ContentForm()
    return render(request, 'superapp/addContentForm.html',
        {
            'form': form,
            'firstName': firstName,
            'lastName': lastName
        }
    )

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
            return redirect('superapp:all-content')
    else:
        form = ContentForm(instance=content)

    return render(request, 'superapp/edit-content.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName,
        'content': content,
    })

def deleteContent(request, id):
    user = request.user
    content = get_object_or_404(TableContent, id=id)
    if request.method == 'POST':
        content.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete content')
        return redirect('superapp:all-content')
    return render(request, 'superapp/allContentPage.html', {'content': content})

def deleteAnnouncement(request, id):
    user = request.user
    announcement = get_object_or_404(TableAnnouncement, id=id)
    if request.method == 'POST':
        announcement.delete()
        saveActivityLogs(user=user, action='DELETE', request=request, description='Delete announcement')
        messages.success(request, 'Announcement has been deleted successfully.')
        return redirect('superapp:getAllTheListAnnouncement')
    return render(
        request, 
        LIST_ANNOUNCEMENT, 
        {
            'announcement': announcement
        }
    )

def editUsers(request, id): 
    toEditDetails = admin = get_object_or_404(CustomUser, pk=id)
    # 
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    # 
    firstName = admin.first_name
    lastName = admin.last_name
    
    if request.method == 'POST':
        form = EditUsersDetailsForm(request.POST, instance=toEditDetails)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='EDIT', request=request, description='Edit users details')
            messages.success(request, 'Profile updated successfully.')
            return redirect('superapp:getAllTheUserAccount')
        else:
            print(form.errors)
    else:
        form = EditUsersDetailsForm(instance=toEditDetails)
    return render(request, 'superapp/edit-users.html', {
        'form': form,
        'admin': admin,
        'toEditDetails': toEditDetails,
        'firstName': firstName,
        'lastName': lastName
    })


def editUserProfile(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    if request.method == 'POST':
        form = EditUsersForm(request.POST, instance=admin)
        if form.is_valid():
            form.save()
            saveActivityLogs(user=user, action='EDIT', request=request, description='Update profile')
            messages.success(request, 'Profile updated successfully.')
            return redirect('superapp:editUserProfile')
    else:
        form = EditUsersForm(instance=admin)
    return render(request, 'superapp/profile.html', {
        'form': form,
        'firstName': firstName,
        'lastName': lastName
    })

def addUsers(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            saveActivityLogs(user=user, action='ADD', request=request, description='Create admin/coordinator account')
            return redirect('superapp:addUsers')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(
        request, 'superapp/add-users.html', 
        {
            'form': form,
            'firstName' : firstName,
            'lastName' : lastName
        }
    )
def createUserAdmin(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            saveActivityLogs(user=user, action='CREATE', request=request, description='Create super credentials')
            return redirect('superapp:createUserAdmin')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    return render(request, 'superapp/userCreation.html', {'form': form})

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
            saveActivityLogs(user=user, action='SET', request=request, description='Set time render')
            return redirect('superapp:set_rendering_hours')
        
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
        
    requirements = TableRequirements.objects.all()
    return render(request, 'superapp/settings.html', {
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
            return redirect('superapp:set_rendering_hours')
    else:
        form = SetRenderingHoursForm()

    return render(request, 'superapp/settings.html', {
        'form': form,
    })
