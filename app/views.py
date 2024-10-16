import re
import os
import json
from typing import Union
from django.urls import reverse
from django.db.models import Sum
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from app.utils import saveActivityLogs
from datetime import datetime, timedelta
from .forms import CustomPasswordChangeForm
from app.forms import SetRenderingHoursForm
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from app.models import CustomUser, TableAnnouncement
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from students.forms import EditStudentForm, ScheduleSettingForm, GradeForm
from app.models import RenderingHoursTable, TableRequirements, TableContent
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, JsonResponse
from app.forms import EditProfileForm, AnnouncementForm, UploadRequirementForm, ContentForm, CustomUserCreationForm
from students.models import DataTableStudents, TimeLog, Schedule, TableSubmittedReport, TableSubmittedRequirement, PendingApplication, RejectApplication, Grade, ReturnToRevisionDocument, ApprovedDocument, LunchLog, Notification

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

@login_required
@csrf_exempt
def dashboard(request) -> HttpResponse:
    return render(request, DASHBOARD)


@login_required
@never_cache
@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def mainDashboard(request):
    # Check if the user is staff but not a superuser
    if not request.user.is_staff or request.user.is_superuser:
        return render(request, 'main/404.html', status=403)

    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    firstName = admin.first_name
    lastName = admin.last_name

    # Default date filters
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())

    # Get filter type from the request
    filter_type = request.GET.get('filterType', 'yesterday')
    start_date = request.GET.get('startDate')
    end_date = request.GET.get('endDate')

    # Apply date filters based on the selected filter type
    if filter_type == 'today':
        approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive', created_at__date=today)
        pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive', created_at__date=today)
        reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive', created_at__date=today)

    elif filter_type == 'yesterday':
        # Use range to capture the entire day of yesterday
        yesterday_start = yesterday
        yesterday_end = today  # This ensures the full range of yesterday
        approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive', created_at__range=(yesterday_start, yesterday_end))
        pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive', created_at__range=(yesterday_start, yesterday_end))
        reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive', created_at__range=(yesterday_start, yesterday_end))

    elif filter_type == 'week':
        approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive', created_at__date__range=(week_start, today))
        pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive', created_at__date__range=(week_start, today))
        reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive', created_at__date__range=(week_start, today))

    elif filter_type == 'custom' and start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        approve = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive', created_at__date__range=(start_date, end_date))
        pending = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive', created_at__date__range=(start_date, end_date))
        reject = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive', created_at__date__range=(start_date, end_date))

    else:
        approve = pending = reject = []

    approve_count = approve.count()
    pending_count = pending.count()
    reject_count = reject.count()

    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'approve_count': approve_count,
            'pending_count': pending_count,
            'reject_count': reject_count,
        })

    return render(
        request,
        'app/main-dashboard.html',
        {
            'approve_count': approve_count,
            'pending_count': pending_count,
            'reject_count': reject_count,
            'firstName': firstName,
            'lastName': lastName
        }
    )

@login_required
@never_cache
def getAllApproveStudents(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)

    firstName = admin.first_name
    lastName = admin.last_name

    # Fetch all approved students
    students_list = DataTableStudents.objects.filter(status='Approved', archivedStudents='NotArchive').order_by('id')

    # Search filter logic
    search_query_approve = request.GET.get('search-approve', '')
    if search_query_approve:
        students_list = students_list.filter(
            Q(StudentID__icontains=search_query_approve) |
            Q(Firstname__icontains=search_query_approve) |
            Q(Middlename__icontains=search_query_approve) |
            Q(Lastname__icontains=search_query_approve)
        )

    # Date filtering logic
    date_filter = request.GET.get('dateFilter', 'today')  # Default to 'today'
    today = timezone.now().date()

    if date_filter == 'today':
        students_list = students_list.filter(created_at__date=today)
    elif date_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        students_list = students_list.filter(created_at__date=yesterday)
    elif date_filter == 'week':
        one_week_ago = today - timedelta(days=7)
        students_list = students_list.filter(created_at__date__gte=one_week_ago)

    # Handle custom date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        students_list = students_list.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

    # Pagination logic
    page = request.GET.get('page', 1)

    # Initialize per_page with a default value
    per_page = 10  # Default value if not provided

    # Get per_page value from request and validate
    per_page_value = request.GET.get('per_page')
    if per_page_value:  # Only set per_page if value is provided
        try:
            per_page = int(per_page_value)  # Convert to int
        except ValueError:
            per_page = 10  # Fall back to default if conversion fails

    paginator = Paginator(students_list, per_page)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        'students': students,
        'firstName': firstName,
        'lastName': lastName,
    }

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/approve-list-student.html', context)

    return render(request, 'app/approve-list-student.html', context)


@login_required
@never_cache
def getAllPendingStudents(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)

    firstName = admin.first_name
    lastName = admin.last_name

    # Fetch all approved students
    students_list = PendingApplication.objects.filter(StatusApplication='PendingApplication', PendingStatusArchive='NotArchive').order_by('id')

    # Search filter logic
    search_query_approve = request.GET.get('search-approve', '')
    if search_query_approve:
        students_list = students_list.filter(
            Q(PendingStudentID__icontains=search_query_approve) |
            Q(PendingFirstname__icontains=search_query_approve) |
            Q(PendingMiddlename__icontains=search_query_approve) |
            Q(PendingLastname__icontains=search_query_approve)
        )

    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))

    paginator = Paginator(students_list, per_page)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        'students': students,
        'firstName': firstName,
        'lastName': lastName,
        'per_page': per_page,
    }

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/pending-list-student.html', context)

    return render(request, 'app/pending-list-student.html', context)

@login_required
@never_cache
def getAllRejectStudents(request):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)

    firstName = admin.first_name
    lastName = admin.last_name

    # Fetch all approved students
    students_list = RejectApplication.objects.filter(RejectStatus='RejectedApplication', RejectStatusArchive='NotArchive').order_by('id')
    archive = DataTableStudents.objects.filter(archivedStudents='Archive').order_by('id')

    # Search filter logic
    search_query_approve = request.GET.get('search-approve', '')
    if search_query_approve:
        students_list = students_list.filter(
            Q(RejectStudentID__icontains=search_query_approve) |
            Q(RejectFirstname__icontains=search_query_approve) |
            Q(RejectMiddlename__icontains=search_query_approve) |
            Q(RejectLastname__icontains=search_query_approve)
        )

    # Pagination logic
    page = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', 10))

    paginator = Paginator(students_list, per_page)
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        'students': students,
        'firstName': firstName,
        'lastName': lastName,
        'per_page': per_page,
    }

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/reject-list-student.html', context)

    return render(request, 'app/reject-list-student.html', context)

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

def return_to_revision(request, id):
    user = request.user
    if request.method == 'POST':
        try:
            submitted_document = TableSubmittedRequirement.objects.get(id=id)
            data = json.loads(request.body)
            reason = data.get('reason', 'No reason provided')
            revision_document = ReturnToRevisionDocument.objects.create(
                nameOfDocs=submitted_document.nameOfDocs,
                student=submitted_document.student,
                revision_file=submitted_document.submitted_file,
                revision_reason=reason
            )
            revision_document.save()
            saveActivityLogs(user=user, action='REVISION', request=request, description='Revision of document')
            submitted_document.delete()
            # Create Notification for Student
            notification_message = f'Your document "{submitted_document.nameOfDocs}" has been returned for revision. Reason: {reason}'
            Notification.objects.create(
                student=submitted_document.student,
                message=notification_message
            )
            # Send email notification
            subject = 'Document Returned for Revision'
            message = render_to_string('app/revision_email.txt', {
                'student_name': submitted_document.student.Firstname,
                'document_name': submitted_document.nameOfDocs,
                'reason': reason,
            })
            recipient_list = [submitted_document.student.Email]
            send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list, fail_silently=False)
            return JsonResponse({'status': 'success', 'message': 'Document returned for revision and student notified.'})
        except TableSubmittedRequirement.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Document does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method.'}, status=405)

def approve_document(request, id):
    user = request.user
    if request.method == 'POST':
        try:
            submitted_document = TableSubmittedRequirement.objects.get(id=id)
            approved_document = ApprovedDocument.objects.create(
                nameOfDocs=submitted_document.nameOfDocs,
                student=submitted_document.student,
                approved_file=submitted_document.submitted_file,
                score=0
            )
            approved_document.save()
            saveActivityLogs(user=user, action='APPROVED', request=request, description='Approve document')
            submitted_document.delete()
            # Create Notification for Student
            notification_message = f'Your document "{submitted_document.nameOfDocs}" has been approved.'
            Notification.objects.create(
                student=submitted_document.student,
                message=notification_message
            )
            return JsonResponse({'status': 'success', 'message': 'Document approved.'})
        except TableSubmittedRequirement.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Document does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method.'}, status=405)

def unArchivedStudent(request, id):
    user = request.user
    student = DataTableStudents.objects.get(id=id)
    student.archivedStudents = 'NotArchive'
    student.save()
    saveActivityLogs(user=user, action='NotArchive', request=request, description='Unarchive students')
    messages.success(request, f'{student.Firstname} {student.Lastname} has been remove to archived.')
    return redirect(reverse('studentManagement'))

def logoutView(request):
    user = request.user
    if user.is_authenticated:
        saveActivityLogs(
            user=user,
            action='LOGOUT',
            request=request,
            description='Logout page'
        )
    logout(request)
    if 'is_logged_in' in request.session:
        del request.session['is_coordinator_logged_in']
    return redirect('homepage:home')

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
    requirements = TableSubmittedRequirement.objects.filter(student=student).order_by('id')
    approve_document = ApprovedDocument.objects.filter(student=student).order_by('id')
    cleaned_reports = [(report, clean_filename(report.report_file.name)) for report in progress_reports]

    context = {
        'firstName': firstName,
        'lastName': lastName,
        'studentFirstname': studentFirstname,
        'studentLastname': studentLastname,
        'cleaned_reports': cleaned_reports,
        'requirements': requirements,
        'approve_document': approve_document
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
        students = students.filter(Q(Firstname__icontains=search_query))
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/grading.html', {'listOfStudents': students})
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page) if per_page else 10
    except ValueError:
        per_page = 10
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


@login_required
def studentInformation(request, id):
    user = request.user
    admin = get_object_or_404(CustomUser, id=user.id)
    student = get_object_or_404(DataTableStudents, id=id)
    
    # Admin and student names
    firstName = admin.first_name
    lastName = admin.last_name
    studentFirstname = student.Firstname
    studentLastname = student.Lastname

    # Fetch logs
    time_logs = TimeLog.objects.filter(student=student).order_by('timestamp')
    lunch_logs = LunchLog.objects.filter(student=student).order_by('timestamp')

    total_work_seconds = 0
    daily_total = timedelta()
    max_work_hours = timedelta(hours=8)
    
    # Calculate total work time and prepare paired logs
    paired_logs = []
    
    for i in range(0, len(time_logs), 2):
        if i + 1 < len(time_logs):
            time_in = time_logs[i].timestamp
            time_out = time_logs[i + 1].timestamp if time_logs[i + 1].action == 'OUT' else None
            
            if time_out:
                work_period = time_out - time_in
                work_period = min(work_period, max_work_hours)  # Cap to max work hours
                daily_total += work_period
                paired_logs.append((time_logs[i], time_logs[i + 1]))  # Pair IN and OUT logs
        else:
            paired_logs.append((time_logs[i], None))  # Add remaining IN log if exists

    # Total work seconds
    total_work_seconds = max(0, daily_total.total_seconds())
    required_hours_seconds = student.get_required_hours() * 3600 if student.get_required_hours() is not None else 0
    remaining_hours_seconds = max(0, required_hours_seconds - total_work_seconds)

    # Handle form submission for any input modifications (if needed)
    if request.method == 'POST':
        total_work_time_input = request.POST.get('total_work_time')
        required_hours_time_input = request.POST.get('required_hours_time')
        remaining_hours_time_input = request.POST.get('remaining_hours_time')
        
        # Assuming you have a method to convert time to seconds, similar to previous function
        total_work_seconds = convert_time_to_seconds(total_work_time_input)
        required_hours_seconds = convert_time_to_seconds(required_hours_time_input)
        remaining_hours_seconds = convert_time_to_seconds(remaining_hours_time_input)

    # Fetch other information
    full_schedule = Schedule.objects.filter(student=student, day__in=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']).order_by('id')
    grades = Grade.objects.filter(student=student).order_by('id')
    progress_reports = TableSubmittedReport.objects.filter(student=student).order_by('-date_submitted', 'id')
    requirements = TableSubmittedRequirement.objects.filter(student=student).order_by('-submission_date', 'id')

    # Clean filenames for progress reports
    cleaned_reports = [(report, clean_filename(report.report_file.name)) for report in progress_reports]

    # Prepare function to format seconds into hours and minutes
    def format_seconds(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes"

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
        'grades': grades,
        'lunch_logs': lunch_logs,
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
    searchgrade = request.GET.get('search-items', '')

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

    # Limit pagination range to 5 pages at a time
    max_display_pages = 5
    current_page = students.number
    total_pages = paginator.num_pages

    # Determine start and end of the pagination range
    start_page = max(current_page - 2, 1)
    end_page = min(start_page + max_display_pages - 1, total_pages)

    if end_page - start_page < max_display_pages:
        start_page = max(end_page - max_display_pages + 1, 1)

    pagination_range = range(start_page, end_page + 1)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'app/grading.html', {'listOfStudents': students})

    return render(request, 'app/grading.html', {
        'listOfStudents': students,
        'withGrade': withGrade,
        'firstName': firstName,
        'lastName': lastName,
        'per_page': per_page,
        'pagination_range': pagination_range,
        'total_pages': total_pages
    })

@require_POST
def update_document_score(request, id):
    try:
        document = ApprovedDocument.objects.get(id=id)
        score = request.POST.get('score')
        if score is None or not score.isdigit() or int(score) < 0 or int(score) > 120:
            messages.error(request, 'Invalid score format. Please enter a score between 0 and 120.')
            return redirect('view-requirements', id=document.student.id)

        document.score = int(score)
        document.save()
        messages.success(request, 'Score updated successfully.')

        total_score = ApprovedDocument.objects.filter(student=document.student).aggregate(total=Sum('score'))['total'] or 0

        grade, created = Grade.objects.get_or_create(student=document.student)

        docs_grade = round((total_score / 120 * 50 + 50) * 0.30, 2) if total_score > 0 else 0
        
        grade.docs = docs_grade
        grade.save()

        return redirect('view-requirements', id=document.student.id)

    except ApprovedDocument.DoesNotExist:
        messages.error(request, 'Document not found.')
        return redirect('view-requirements', id=id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('view-requirements', id=id)

def gradeFormula(evaluation, docs_grade, oral_interview):
    eval_score = (evaluation / 30 * 50 + 50) * 0.60
    docs_score = docs_grade
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
    grade, created = Grade.objects.get_or_create(student=student)
    total_docs_score = ApprovedDocument.objects.filter(student=student).aggregate(total=Sum('score'))['total'] or 0

    total_eval_score = Grade.objects.filter(student__id=id).values_list('evaluation', flat=True)
    total_oral_score = Grade.objects.filter(student__id=id).values_list('oral_interview', flat=True)

    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            evaluation = min(max(form.cleaned_data['evaluation'], 0), 30)
            oral_interview = min(max(form.cleaned_data['oral_interview'], 0), 30)
            
            # Calculate and round the scores to one decimal place
            eval_score = round((evaluation / 30 * 50 + 50) * 0.60, 1)
            docs_score = round((total_docs_score / 120 * 50 + 50) * 0.30, 1) if total_docs_score > 0 else 0
            oral_score = round((oral_interview / 30 * 50 + 50) * 0.10, 1)

            # Update the Grade object with rounded scores
            grade.evaluation = eval_score
            grade.docs = docs_score
            grade.oral_interview = oral_score

            # Calculate the final grade and round it to one decimal place
            final_grade = round(eval_score + docs_score + oral_score, 1)
            grade.final_grade = final_grade
            grade.status = 'Passed' if final_grade > 74 else 'Failed'
            grade.save()

            return render(request, 'app/computeGradePage.html', {
                'form': form,
                'student': student,
                'final_grade': final_grade,
                'status': grade.status,
                'gradesResult': [grade],
            })
    else:
        form = GradeForm(initial={
            'evaluation': grade.evaluation,
            'docs': grade.docs,
            'oral_interview': grade.oral_interview
        })

    return render(
        request,
        'app/computeGradePage.html',
        {
            'form': form,
            'final_grade': final_grade,
            'student': student,
            'status': status,
            'firstName': firstName,
            'lastName': lastName,
            'gradesResult': [grade],
            'total_score': total_docs_score,
            'total_eval_score': total_eval_score,
            'total_oral_score': total_oral_score,
            'grade': grade
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
