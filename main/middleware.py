# main/middleware.py

from django.shortcuts import redirect, render
import logging

logger = logging.getLogger(__name__)

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Redirect if user is authenticated and trying to access login pages
        if request.user.is_authenticated:
            # Check if the user is trying to access the login pages
            if request.path in ['/students/login/', '/coordinator/login/']:
                return redirect('/students/dashboard/') if 'students' in request.path else redirect('/coordinator/mainDashboard')
            
            # Optionally, prevent access to the homepage if already logged in
            elif request.path == '/':
                return redirect('/students/dashboard/')  # Or the appropriate landing page for logged-in users

        # Proceed with the request and get the response
        response = self.get_response(request)

        # Log the response for 404 errors
        if response.status_code == 404:
            logger.error(f"Page not found: {request.path}")
            return render(request, '404.html', status=404)

        return response
