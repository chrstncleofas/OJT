from django import forms
from app.models import CustomUser
from students.models import DataTableStudents, TimeLog, Schedule
from students.custom_widgets import CustomClearableFileInput

COURSE_CHOICES = [
    ('', '--- Select Course ---'),
    ('BS Computer Science', 'BS Computer Science'),
    ('BS Information Technology', 'BS Information Technology'),
]

PREFIX_CHOICES = [
    ('', '--- Select Prefix ---'),
    ('Jr', 'Jr'),
    ('III', 'III'),
    ('Senior', 'Senior'),
]

YEAR_CHOICES = [
    ('', '--- Select Year ---'),
    ('4th', '4th'),
    ('3rd', '3rd'),
    ('2nd', '2nd'),
    ('1st', '1st'),
]

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Create a password'}
        )
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Re-type your password'}
        )
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = cleaned_data.get("email")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password and Confirm Password do not match")

        if CustomUser.objects.filter(email=email).exists():
            self.add_error('email', "Email already exists. Please use a different email address.")
        
        return cleaned_data

class StudentRegistrationForm(forms.ModelForm):
    StudentID = forms.CharField(
        max_length=16, 
        label='Student ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. 18-0000'})
    )

    Course = forms.ChoiceField(
        choices=COURSE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    Prefix = forms.ChoiceField(
        choices=PREFIX_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    Number = forms.CharField(
        max_length=11, 
        label='Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. 09610090120'})
    )

    Year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = DataTableStudents
        fields = ['StudentID', 'Firstname', 'Middlename', 'Lastname', 'Prefix', 'Address', 'Number' ,'Course', 'Year']
        widgets = {
            'Firstname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}),
            'Middlename': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Middle Name'}),
            'Lastname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'}),
            'Address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full Address'}),
        }

    def __init__(self, *args, **kwargs):
        super(StudentRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['Firstname'].required = True
        self.fields['Middlename'].required = False
        self.fields['Lastname'].required = True
        self.fields['Course'].required = True
        self.fields['Year'].required = True


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = DataTableStudents
        fields = ['Firstname', 'Lastname', 'Email', 'Course', 'Year', 'Image']
        widgets = {
            'Firstname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}),
            'Lastname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'}),
            'Email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email'}),
            'Course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Course'}),
            'Year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Year'}),
            'Image': CustomClearableFileInput,
        }

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "New password and confirm password do not match")

        return cleaned_data

class TimeLogForm(forms.ModelForm):
    class Meta:
        model = TimeLog
        fields = ['image', 'action']

    def __init__(self, *args, **kwargs):
        super(TimeLogForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = True
        self.fields['image'].widget.attrs.update({'accept': 'image/*'})
        self.fields['action'].widget = forms.HiddenInput()

class EditStudentForm(forms.ModelForm):
    class Meta:
        model = DataTableStudents
        fields = ['Firstname', 'Middlename', 'Lastname', 'Email', 'Course', 'Year', 'status']
        widgets = {
            'Firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'Middlename': forms.TextInput(attrs={'class': 'form-control'}),
            'Lastname': forms.TextInput(attrs={'class': 'form-control'}),
            'Email': forms.EmailInput(attrs={'class': 'form-control'}),
            'Course': forms.TextInput(attrs={'class': 'form-control'}),
            'Year': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class ScheduleSettingForm(forms.Form):
    monday_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    monday_end = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    tuesday_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    tuesday_end = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    wednesday_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    wednesday_end = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    thursday_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    thursday_end = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    friday_start = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
    friday_end = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}), required=False)
