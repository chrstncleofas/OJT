from django import forms
from app.models import CustomUser
from students.custom_widgets import CustomClearableFileInput
from students.models import DataTableStudents,\
    TimeLog,\
    TableSubmittedRequirement,\
    PendingApplication,\
    Grade,\
    LunchLog,\
    ApprovedDocument

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

class PendingStudentRegistrationForm(forms.ModelForm):
    PendingStudentID = forms.CharField(
        max_length=16, 
        label='Student ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. 18-0000'})
    )

    PendingCourse = forms.ChoiceField(
        choices=COURSE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    PendingPrefix = forms.ChoiceField(
        choices=PREFIX_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    PendingNumber = forms.CharField(
        max_length=11, 
        label='Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex. 09610090120'})
    )

    PendingYear = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    PendingPassword = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        label='Password'
    )

    confirmPassword = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Re-type your password'}
        )
    )

    class Meta:
        model = PendingApplication
        fields = ['PendingStudentID', 'PendingFirstname', 'PendingMiddlename', 'PendingLastname', 'PendingPrefix', 'PendingEmail', 'PendingAddress', 'PendingNumber' ,'PendingCourse', 'PendingYear', 'PendingUsername', 'PendingPassword']
        widgets = {
            'PendingFirstname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}),
            'PendingMiddlename': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Middle Name'}),
            'PendingLastname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Last Name'}),
            'PendingAddress': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full Address'}),
            'PendingEmail': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email'}),
            'PendingUsername': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("PendingPassword")
        confirm_password = cleaned_data.get("confirmPassword")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirmPassword', "Password and Confirm Password do not match")

    def __init__(self, *args, **kwargs):
        super(PendingStudentRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['PendingFirstname'].required = True
        self.fields['PendingMiddlename'].required = False
        self.fields['PendingLastname'].required = True
        self.fields['PendingCourse'].required = True
        self.fields['PendingYear'].required = True

    
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

class LunchLogForm(forms.ModelForm):
    class Meta:
        model = LunchLog
        fields = ['image', 'action']
    def __init__(self, *args, **kwargs):
        super(LunchLogForm, self).__init__(*args, **kwargs)
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

class ProgressReportForm(forms.Form):
    INTERNSHIP_CHOICE = [
        ('local', 'Local'),
        ('international', 'International'),
    ]

    LOCAL_CONDITION = [
        ('inCampus', 'In Campus'),
        ('offCampus', 'Off Campus'),
    ]

    MODALITY_CHOICES = [
        ('actual', 'Actual Internship'),
        ('virtual', 'Virtual Internship'),
    ]

    VIRTUAL_CHOICE = [
        ('wfh', 'WFH Arrangement'),
        ('under', 'Under Alternative Activities')
    ]

    student_name = forms.CharField(label='Name of Student', max_length=100, required=False)
    internship_classification = forms.ChoiceField(
        label='Internship Classification',
        choices=INTERNSHIP_CHOICE,
        widget=forms.RadioSelect,
        required=False
    )

    local_condition = forms.ChoiceField(
        label='Local Condition',
        choices=LOCAL_CONDITION,
        widget=forms.RadioSelect,
        required=False
    )
    
    internship_modality = forms.ChoiceField(
        label='Internship Modality',
        choices=MODALITY_CHOICES,
        widget=forms.RadioSelect,
        required=False
    )

    virtual_conditions = forms.ChoiceField(
        label='Virtual Conditions',
        choices=VIRTUAL_CHOICE,
        widget=forms.RadioSelect,
        required=False
    )

    hte_name = forms.CharField(label='Host Training Establishment', max_length=100, required=False)
    hte_address = forms.CharField(label='Address of Host Training Establishment', max_length=255, required=False)
    department_division = forms.CharField(label='Department Division Assigned', max_length=100, required=False)

    # Monday
    monday_date = forms.DateField(label='Monday Date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    monday_description = forms.CharField(label='Monday Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    monday_hours = forms.IntegerField(label='Monday Hours', required=False)
    # Tuesday
    tuesday_date = forms.DateField(label='Tuesday Date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    tuesday_description = forms.CharField(label='Tuesday Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    tuesday_hours = forms.IntegerField(label='Tuesday Hours', required=False)
    # Wednesday
    wednesday_date = forms.DateField(label='Wednesday Date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    wednesday_description = forms.CharField(label='Wednesday Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    wednesday_hours = forms.IntegerField(label='Wednesday Hours', required=False)
    # Thursday
    thursday_date = forms.DateField(label='Thursday Date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    thursday_description = forms.CharField(label='Thursday Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    thursday_hours = forms.IntegerField(label='Thursday Hours', required=False)
    # Friday
    friday_date = forms.DateField(label='Friday Date', required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    friday_description = forms.CharField(label='Friday Description', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    friday_hours = forms.IntegerField(label='Friday Hours', required=False)


class SubmittedRequirement(forms.ModelForm):
    REQUIRED_DOCS = [
        ('', '--- Select Document ---'),
        ('Application Form', 'Application Form'),
        ('Endorsement Letter', 'Endorsement Letter'),
        ('Internship Contract Agreement', 'Internship Contract Agreement'),
        ('Medical Certificate', 'Medical Certificate'),
        ('Notice of Acceptance / MOA', 'Notice of Acceptance / MOA'),
        ('Parent Consent', 'Parent Consent'),
        ('Evaluation Form', 'Evaluation Form'),
        ('Progress Report', 'Progress Report'),
        ('Internship Time Sheet', 'Internship Time Sheet'),
        ('Internship Exit Survey', 'Internship Exit Survey'),
        ('Student Performance Evaluation', 'Student Performance Evaluation'),
        ('Supporting Document of Time Sheet', 'Supporting Document of Time Sheet'),
        ('Supporting Document of Progress Report', 'Supporting Document of Progress Report'),
    ]

    nameOfDocs = forms.ChoiceField(
        choices=[],
        label="Select Requirement",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TableSubmittedRequirement
        fields = ['nameOfDocs', 'submitted_file']

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super(SubmittedRequirement, self).__init__(*args, **kwargs)

        if student:
            submitted_docs = TableSubmittedRequirement.objects.filter(student=student).values_list('nameOfDocs', flat=True)
            approved_docs = ApprovedDocument.objects.filter(student=student).values_list('nameOfDocs', flat=True)
            remaining_docs = [doc for doc in self.REQUIRED_DOCS if doc[0] not in submitted_docs and doc[0] not in approved_docs]

            # Set the available choices for the dropdown
            self.fields['nameOfDocs'].choices = remaining_docs
        else:
            self.fields['nameOfDocs'].choices = self.REQUIRED_DOCS

        # Customize file input
        self.fields['submitted_file'].widget.attrs.update({
            'accept': 'application/pdf',
            'class': 'form-control-file'
        })

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['evaluation', 'docs', 'oral_interview']
        widgets = {
            'evaluation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter evaluation score'}),
            'docs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter docs score'}),
            'oral_interview': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter oral interview score'}),
        }

    def __init__(self, *args, **kwargs):
        super(GradeForm, self).__init__(*args, **kwargs)
        self.fields['evaluation'].required = True
        self.fields['docs'].required = False
        self.fields['oral_interview'].required = True

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password', 'min_length': 8})
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password', 'min_length': 8})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")