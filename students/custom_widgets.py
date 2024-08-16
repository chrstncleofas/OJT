
from django.forms import ClearableFileInput

class CustomClearableFileInput(ClearableFileInput):
    template_name = 'students/custom_clearable_file_input.html'
