import logging
from app.models import CustomUser
from students.models import DataTableStudents
from django.shortcuts import redirect, render
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

def is_student(user):
    """
    Check if the user is a student.
    Returns True if the user is a student, otherwise False.
    """
    try:
        DataTableStudents.objects.get(user=user)
        return True
    except DataTableStudents.DoesNotExist:
        return False

def is_coordinator(user):
    """
    Check if the user is a coordinator (staff but not superuser).
    Returns True if the user is a coordinator, otherwise False.
    """
    return isinstance(user, CustomUser) and user.is_staff and not user.is_superuser

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Redirect authenticated users trying to access login pages or homepage
        if request.user.is_authenticated:
            # Check if the user is trying to access the login pages
            if request.path in ['/students/login/', '/coordinator/login/']:
                # Redirect students and coordinators to their respective dashboards
                if 'students' in request.path:
                    return redirect('/students/dashboard/')
                elif 'coordinator' in request.path:
                    return redirect('/coordinator/dashboard')

            # Redirect logged-in users away from the homepage to their respective dashboards
            elif request.path == '/':
                if is_student(request.user):
                    return redirect('/students/dashboard/')
                elif is_coordinator(request.user):
                    return redirect('/coordinator/dashboard')

        # Handle the response and log 404 errors if any
        response = self.get_response(request)

        if response.status_code == 404:
            logger.error(f"Page not found: {request.path}")
            return render(request, 'main/404.html', status=404)

        return response

class CrossOriginOpenerPolicyMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Cross-Origin-Opener-Policy'] = 'unsafe-none'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        return response