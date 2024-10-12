from django.http import JsonResponse
from app.utils import saveActivityLogs
from app.models import TableAnnouncement
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from students.models import PendingApplication, DataTableStudents

def homePage(request):
    return render(request, 'homepage/home-page.html')

@never_cache
@csrf_protect
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
                    return JsonResponse({'error': 'Your account has been rejected. Please contact the admin for further details.'})
                elif student.archivedStudents == 'Archive':
                    return JsonResponse({'error': 'Your account has been locked due to inactivity. Please contact your admin.'})
                if user.is_active:
                    login(request, user)
                    request.session['is_logged_in'] = True
                    return JsonResponse({'redirect_url': '/students/dashboard/'})
            except DataTableStudents.DoesNotExist:
                return JsonResponse({'error': 'Student account not found.'})
        else:
            return JsonResponse({'error': 'Invalid username or password.'})
    return render(request, 'homepage/home-page.html')

@never_cache
@csrf_protect
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
                    request.session['is_logged_in'] = True
                    request.session['admin_password'] = user.password
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
