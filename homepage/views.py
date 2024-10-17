from functools import wraps
from django.urls import reverse
from django.conf import settings
from django.contrib import messages  
from django.http import JsonResponse
from app.utils import saveActivityLogs
from django.core.mail import send_mail
from app.models import TableAnnouncement
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_control
from students.models import PendingApplication, DataTableStudents
from app.models import TableContent, TableAnnouncement
from students.forms import PendingStudentRegistrationForm, ResetPasswordForm

def redirect_authenticated_user(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'datatablestudents'):
                return redirect('students:dashboard')
            elif request.user.is_staff and not request.user.is_superuser:
                return redirect('mainDashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@never_cache
@csrf_protect
@cache_control(no_cache=True, must_revalidate=True, no_store=True, name='dispatch')
def webPage(request):
    images = TableContent.objects.all().order_by('id')
    announcements = TableAnnouncement.objects.all().order_by('id')
    return render(
        request, 'homepage/main-page.html',
        {
            'images': images,
            'announcements': announcements
        }
    )

@redirect_authenticated_user
@never_cache
@csrf_protect
@cache_control(no_cache=True, must_revalidate=True, no_store=True, name='dispatch')
def homePage(request):
    return render(request, 'homepage/home-page.html')

@redirect_authenticated_user
@never_cache
@csrf_protect
@cache_control(no_cache=True, must_revalidate=True, no_store=True, name='dispatch')
def studentLogin(request):
    if request.user.is_authenticated:
        return redirect('students:dashboard')
    if request.method == 'POST':
        username = request.POST.get('Username')
        password = request.POST.get('Password')
        pending_app = PendingApplication.objects.filter(PendingUsername=username, StatusApplication="PendingApplication").first()
        if pending_app:
            return JsonResponse({'error': 'Your account is not yet approved. Please wait for admin approval.'})
        user = authenticate(request, username=username, password=password)
        if user:
            try:
                student = DataTableStudents.objects.get(user=user)
                if student.status == 'RejectedApplication':
                    return JsonResponse({'error': 'Your account has been rejected. Please contact the admin.'})
                elif student.archivedStudents == 'Archive':
                    return JsonResponse({'error': 'Your account has been locked due to inactivity. Please contact your admin.'})
                if user.is_active:
                    login(request, user)
                    request.session['is_student_logged_in'] = True
                    return JsonResponse({'redirect_url': '/students/dashboard/'})
            except DataTableStudents.DoesNotExist:
                return JsonResponse({'error': 'Student account not found.'})
        else:
            return JsonResponse({'error': 'Invalid username or password.'})
    return render(request, 'homepage/home-page.html')

@redirect_authenticated_user
@never_cache
@csrf_protect
@cache_control(no_cache=True, must_revalidate=True, no_store=True, name='dispatch')
def coordinatorLogin(request):
    if request.user.is_authenticated:
        return redirect('mainDashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_staff and not user.is_superuser:
                if user.is_active:
                    login(request, user)
                    request.session['is_coordinator_logged_in'] = True
                    saveActivityLogs(user=user, action='LOGIN', request=request, description='Login admin/coordinator')
                    return JsonResponse({'redirect_url': '/coordinator/mainDashboard'})
            else:
                return JsonResponse({'error': 'You do not have the necessary permissions to access this site.'})
        else:
            return JsonResponse({'error': 'Invalid username or password.'})
    return render(request, 'homepage/home-page.html')

def getAnnouncement(request):
    enabledAnnouncement = TableAnnouncement.objects.filter(Status='enable')
    return render(
        request, 'homepage/announcement-page.html', 
        {
            'announcements': enabledAnnouncement
        }
    )

@never_cache
def studentRegister(request):
    if request.method == 'POST':
        pending_registration_form = PendingStudentRegistrationForm(request.POST)
        if pending_registration_form.is_valid():
            studentId = pending_registration_form.cleaned_data['PendingStudentID']
            email = pending_registration_form.cleaned_data['PendingEmail']
            username = pending_registration_form.cleaned_data['PendingUsername']
            phone_number = pending_registration_form.cleaned_data['PendingNumber']
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
                message = render_to_string('homepage/registration_email.txt', {
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
                return redirect('homepage:student-register')
    else:
        pending_registration_form = PendingStudentRegistrationForm()

    return render(
        request, 'homepage/register.html', 
        {
            'pending_registration_form': pending_registration_form
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
            reset_link = request.build_absolute_uri(reverse('homepage:reset_password', args=[token]))
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )
            messages.success(request, 'Password reset link has been sent to your email.')
        else:
            messages.error(request, 'Email not found.')
    return render(request, 'homepage/forgot_password.html')

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
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResetPasswordForm()
    return render(request, 'homepage/reset_password.html', {'form': form, 'token': token})