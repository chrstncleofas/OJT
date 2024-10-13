from django.shortcuts import redirect, render
import logging
from students.models import DataTableStudents
from app.models import CustomUser

logger = logging.getLogger(__name__)

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
                    return redirect('/coordinator/mainDashboard')

            # Redirect logged-in users away from the homepage to their respective dashboards
            elif request.path == '/':
                try:
                    # Check if the user is a student
                    student = DataTableStudents.objects.get(user=request.user)
                    return redirect('/students/dashboard/')
                except DataTableStudents.DoesNotExist:
                    pass  # The user is not a student

                # Check if the user is a coordinator (staff but not superuser)
                if isinstance(request.user, CustomUser) and request.user.is_staff and not request.user.is_superuser:
                    return redirect('/coordinator/mainDashboard')

        # Handle the response and log 404 errors if any
        response = self.get_response(request)

        if response.status_code == 404:
            logger.error(f"Page not found: {request.path}")
            return render(request, '404.html', status=404)

        return response
