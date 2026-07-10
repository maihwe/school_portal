from django.contrib import admin
from .models import StudentProfile, ExamResult, SchoolFeeInvoice

admin.site.register(StudentProfile)
admin.site.register(ExamResult)
admin.site.register(SchoolFeeInvoice)
