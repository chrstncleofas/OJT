
from django.forms import ClearableFileInput

class CustomClearableFileInput(ClearableFileInput):
    template_name = 'app/custom_clearable_file_input.html'
