from django.shortcuts import render
from django.http import HttpResponse

def studentHome(request) -> HttpResponse:
    return render(request, 'students/student-base.html')
