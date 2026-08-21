from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from portal.models import StudentProfile, ExamResult, SchoolFeeInvoice

class Command(BaseCommand):
    help = 'Create a demo student account for testing the portal'
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='demo.student', defaults={'first_name':'Amaka','last_name':'Peter','email':'amaka@example.com'})
        user.first_name, user.last_name = 'Amaka', 'Peter'
        user.set_password('EPMdemo2026!')
        user.save()
        student, _ = StudentProfile.objects.get_or_create(user=user, defaults={'student_id':'EPM/2026/0042','current_class':'SS 2','result_pin':'123456789012'})
        student.student_id = 'EPM/2026/0042'
        student.current_class = 'SS 2'
        student.result_pin = '123456789012'; student.save()
        if not ExamResult.objects.filter(student=student).exists():
            for subject, ca, exam in [('Mathematics',27,61),('English Language',25,58),('Biology',26,63),('Physics',24,55)]:
                ExamResult.objects.create(student=student, class_level='SS 2', subject=subject, continuous_assessment=ca, exam_score=exam, term='First', session='2026/2027')
        ExamResult.objects.filter(student=student).update(class_level='SS 2')
        SchoolFeeInvoice.objects.get_or_create(student=student, title='First Term Tuition & Development Levy', defaults={'amount':185000})
        admin, _ = User.objects.get_or_create(username='demo.admin')
        admin.first_name, admin.last_name = 'School', 'Administrator'
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password('AdminDemo2026!')
        admin.save()
        self.stdout.write(self.style.SUCCESS('Student: demo.student / EPMdemo2026! | Result PIN: 123456789012'))
        self.stdout.write(self.style.SUCCESS('Administrator: demo.admin / AdminDemo2026!'))
