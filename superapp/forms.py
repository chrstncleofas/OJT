from django import forms
from django.contrib.auth import get_user_model

ROLE_OPTION = [
    ('', '--- Select Role ---'),
    ('Super Admin', 'Super Admin'),
    ('Admin', 'Admin'),
    ('Coordinator', 'Coordinator'),
]

class SuperuserForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class EditUsersForm(forms.ModelForm):

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

