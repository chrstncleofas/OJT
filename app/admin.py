from django import forms
from django.contrib import admin
from app.forms import AnnouncementForm
from django.contrib.auth.admin import UserAdmin
from app.models import CustomUser, Announcement

class CustomUserAdmin(UserAdmin):
    model = CustomUser

class AnnouncementAdmin(admin.ModelAdmin):
    form = AnnouncementForm
    list_display = ('Title', 'Date', 'Status', 'Category')
    list_filter = ('Status', 'Category')
    search_fields = ('Title', 'Description')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'Date':
            kwargs['widget'] = forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Announcement, AnnouncementAdmin)