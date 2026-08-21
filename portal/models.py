from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

CLASS_CHOICES = [
    ('JSS 1', 'JSS 1'), ('JSS 2', 'JSS 2'), ('JSS 3', 'JSS 3'),
    ('SS 1', 'SS 1'), ('SS 2', 'SS 2'), ('SS 3', 'SS 3'),
]

SUBJECT_CHOICES = [
    ('Junior Secondary (JSS)', [
        ('English Studies', 'English Studies'), ('Mathematics', 'Mathematics'),
        ('Basic Science', 'Basic Science'), ('Basic Technology', 'Basic Technology'),
        ('National Values Education', 'National Values Education'),
        ('Civic Education', 'Civic Education'), ('Social Studies', 'Social Studies'),
        ('Security Education', 'Security Education'),
        ('Cultural and Creative Arts', 'Cultural and Creative Arts'),
        ('Business Studies', 'Business Studies'),
        ('Pre-Vocational Studies', 'Pre-Vocational Studies'),
        ('Agricultural Science', 'Agricultural Science'), ('Home Economics', 'Home Economics'),
        ('Computer Studies / ICT', 'Computer Studies / ICT'),
        ('Physical and Health Education', 'Physical and Health Education'),
        ('Christian Religious Studies', 'Christian Religious Studies'),
        ('Islamic Studies', 'Islamic Studies'), ('French', 'French'),
        ('Arabic', 'Arabic'), ('Hausa', 'Hausa'), ('Igbo', 'Igbo'), ('Yoruba', 'Yoruba'),
    ]),
    ('Senior Secondary - Compulsory', [
        ('English Language', 'English Language'), ('General Mathematics', 'General Mathematics'),
        ('Civic Education', 'Civic Education'), ('Trade / Entrepreneurship', 'Trade / Entrepreneurship'),
    ]),
    ('Senior Secondary - Sciences', [
        ('Biology', 'Biology'), ('Chemistry', 'Chemistry'), ('Physics', 'Physics'),
        ('Further Mathematics', 'Further Mathematics'),
        ('Agricultural Science', 'Agricultural Science'),
        ('Health Education', 'Health Education'), ('Physical Education', 'Physical Education'),
        ('Computer Studies', 'Computer Studies'), ('Data Processing', 'Data Processing'),
        ('Food and Nutrition', 'Food and Nutrition'),
    ]),
    ('Senior Secondary - Humanities', [
        ('Literature in English', 'Literature in English'), ('Government', 'Government'),
        ('History', 'History'), ('Geography', 'Geography'),
        ('Christian Religious Studies', 'Christian Religious Studies'),
        ('Islamic Studies', 'Islamic Studies'), ('French', 'French'),
        ('Hausa', 'Hausa'), ('Igbo', 'Igbo'), ('Yoruba', 'Yoruba'),
        ('Visual Art', 'Visual Art'), ('Music', 'Music'),
    ]),
    ('Senior Secondary - Business', [
        ('Economics', 'Economics'), ('Commerce', 'Commerce'),
        ('Financial Accounting', 'Financial Accounting'),
        ('Office Practice', 'Office Practice'), ('Insurance', 'Insurance'),
        ('Store Management', 'Store Management'),
    ]),
    ('Senior Secondary - Trade / Vocational', [
        ('Marketing', 'Marketing'), ('Catering Craft Practice', 'Catering Craft Practice'),
        ('Garment Making', 'Garment Making'), ('Animal Husbandry', 'Animal Husbandry'),
        ('Fisheries', 'Fisheries'), ('Auto Mechanics', 'Auto Mechanics'),
        ('Electrical Installation', 'Electrical Installation'),
        ('Technical Drawing', 'Technical Drawing'), ('Woodwork', 'Woodwork'),
        ('Building Construction', 'Building Construction'),
    ]),
]

SESSION_CHOICES = [(f'{year}/{year + 1}', f'{year}/{year + 1}') for year in range(2010, 2041)]

# 1. Student Profile with Passport Photo and Pin Access
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=60, blank=True, verbose_name='Middle name')
    student_id = models.CharField(max_length=15, unique=True, verbose_name="Admission Number")
    current_class = models.CharField(max_length=20, choices=CLASS_CHOICES)
    passport_photo = models.ImageField(upload_to='passports/', blank=True, null=True)
    result_pin = models.CharField(max_length=12, help_text="12-digit Scratch Card PIN to view results", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

# 2. Academic Results
class ExamResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    class_level = models.CharField(max_length=20, choices=CLASS_CHOICES, default='JSS 1')
    subject = models.CharField(max_length=60, choices=SUBJECT_CHOICES)
    continuous_assessment = models.IntegerField(default=0, verbose_name="CA Score (30)", validators=[MinValueValidator(0), MaxValueValidator(30)])
    exam_score = models.IntegerField(default=0, verbose_name="Exam Score (70)", validators=[MinValueValidator(0), MaxValueValidator(70)])
    term = models.CharField(max_length=15, choices=[('First', 'First Term'), ('Second', 'Second Term'), ('Third', 'Third Term')])
    session = models.CharField(max_length=15, choices=SESSION_CHOICES, default='2026/2027')

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
