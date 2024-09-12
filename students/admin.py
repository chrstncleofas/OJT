from django import forms
from django.contrib import admin
from django.utils.html import format_html
from students.models import TableSubmittedReport

class TableSubmittedReportAdmin(admin.ModelAdmin):
    list_display = ('student', 'report_file_name_link', 'date_submitted')
    list_filter = ('date_submitted',)  # Use 'date_submitted' for filtering
    search_fields = ('student__username', 'report_file')  # Adjust search fields as needed

    def report_file_name_link(self, obj):
        if obj.report_file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.report_file.url,
                obj.report_file.name
            )
        return "No file"

    report_file_name_link.short_description = 'Progress Report'

    def date_submitted(self, obj):
        if obj.date_submitted:
            return obj.date_submitted.strftime('%b %d, %Y %H:%M:%S')  # Format the date as needed
        return "Not available"

    date_submitted.short_description = 'Date Submitted'

admin.site.register(TableSubmittedReport, TableSubmittedReportAdmin)
