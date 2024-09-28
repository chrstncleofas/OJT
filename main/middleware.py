# my_project/middleware.py

from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log the response for 404 errors
        if response.status_code == 404:
            logger.error(f"Page not found: {request.path}")
            return render(request, '404.html', status=404)  # Updated to use '404.html' directly

        return response
