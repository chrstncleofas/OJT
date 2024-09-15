from django import forms
from app.models import TableAnnouncement
from app.models import RenderingHoursTable, TableRequirements
from django.contrib.auth import get_user_model
from app.custom_widgets import CustomClearableFileInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordChangeForm

STATUS = [
    ('enable', 'Enable'),
    ('disable', 'Disable'),
]

ROLE_OPTION = [
    ('', '--- Select Role ---'),
    ('Super Admin', 'Super Admin'),
    ('Admin', 'Admin'),
    ('Coordinator', 'Coordinator'),
]

CATEGGORY_SELECTION = [
    ('', '--- Select Category ---'),
    ('What', 'What'),
    ('When', 'When'),
    ('Where', 'Where'),
    ('Who', 'Who'),
]

class CustomUserCreationForm(UserCreationForm):

    position = position = forms.ChoiceField(
        choices=ROLE_OPTION,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'position']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'position']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        fields = ['old_password', 'new_password1', 'new_password2']

class AnnouncementForm(forms.ModelForm):
    Status = forms.ChoiceField(
        choices=STATUS,  # Assuming STATUS is defined elsewhere
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TableAnnouncement
        fields = ['Title', 'Image', 'StartDate', 'EndDate', 'Description', 'Status']
        widgets = {
            'Title': forms.TextInput(attrs={'class': 'form-control', 'max_length': 100}),
            'Description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'max_length': 450}),
            'Image': CustomClearableFileInput,
            'StartDate': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'EndDate': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)
        self.fields['Title'].required = True
        self.fields['Description'].required = True
        self.fields['StartDate'].required = True
        self.fields['EndDate'].required = True

class EditUsersDetailsForm(forms.ModelForm):

    position = forms.ChoiceField(
        choices=ROLE_OPTION,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email', 'position']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class UploadRequirementForm(forms.ModelForm):
    class Meta:
        model = TableRequirements
        fields = ['nameOfFile', 'document']
        widgets = {
            'nameOfFile': forms.TextInput(attrs={'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RenderingHoursForm(forms.ModelForm):
    class Meta:
        model = RenderingHoursTable
        fields = ['course', 'required_hours']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'required_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SetRenderingHoursForm(forms.Form):
    bsit_hours = forms.IntegerField(
        label='BS Information Technology',
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    bscs_hours = forms.IntegerField(
        label='BS Computer Science',
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )