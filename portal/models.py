from django.db import models
from django.contrib.auth.models import User

# 1. Student Profile with Passport Photo and Pin Access
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=15, unique=True, verbose_name="Admission Number")
    current_class = models.CharField(max_length=20, choices=[
        ('JSS 1', 'JSS 1'), ('JSS 2', 'JSS 2'), ('JSS 3', 'JSS 3'),
        ('SS 1', 'SS 1'), ('SS 2', 'SS 2'), ('SS 3', 'SS 3')
    ])
    passport_photo = models.ImageField(upload_to='passports/', blank=True, null=True)
    result_pin = models.CharField(max_length=12, help_text="12-digit Scratch Card PIN to view results", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

# 2. Academic Results
class ExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.CharField(max_length=50, choices=[
        ('Mathematics', 'Mathematics'), ('English Language', 'English Language'),
        ('Basic Science', 'Basic Science'), ('Civic Education', 'Civic Education'),
        ('Biology', 'Biology'), ('Chemistry', 'Chemistry'), ('Physics', 'Physics')
    ])
    continuous_assessment = models.IntegerField(default=0, verbose_name="CA Score (30)")
    exam_score = models.IntegerField(default=0, verbose_name="Exam Score (70)")
    term = models.CharField(max_length=15, choices=[('First', 'First Term'), ('Second', 'Second Term'), ('Third', 'Third Term')])
    session = models.CharField(max_length=15, help_text="e.g. 2026/2027")

    @property
    def total_score(self):
        return self.continuous_assessment + self.exam_score

    def __str__(self):
        return f"{self.student.student_id} - {self.subject} ({self.term} Term)"

# 3. Fees and Invoice Tracking
class SchoolFeeInvoice(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default="Term Tuition Fees")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"{self.student.user.last_name} - {self.title} ({status})"
