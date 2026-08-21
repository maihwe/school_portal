from datetime import date

from django import forms
from django.contrib import admin
from .models import StudentProfile, ExamResult, SchoolFeeInvoice

admin.site.site_header = "Edor Peter's Memorial School"
admin.site.site_title = "EPM School Management"
admin.site.index_title = "School Management Portal"


class StudentProfileAdminForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.SelectDateWidget(
                years=range(date.today().year, 1949, -1)
            ),
        }


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    form = StudentProfileAdminForm
    list_display = ('student_id', 'user', 'middle_name', 'current_class', 'date_of_birth')
    list_filter = ('current_class',)
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name')
    date_hierarchy = 'date_of_birth'


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_level', 'subject', 'term', 'session', 'total_score')
    list_filter = ('class_level', 'term', 'session', 'subject')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name')
    ordering = ('-session', 'class_level', 'student', 'subject')

admin.site.register(SchoolFeeInvoice)
