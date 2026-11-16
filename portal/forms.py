from uuid import uuid4

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.db import transaction
from django.utils import timezone

from .models import StudentProfile


class PortalAuthenticationForm(AuthenticationForm):
    """Accept a student's admission number as well as their existing username."""

    def clean(self):
        identifier = self.cleaned_data.get('username')
        # Keep existing usernames authoritative if an admission number overlaps.
        if identifier and not get_user_model().objects.filter(username=identifier).exists():
            try:
                student = StudentProfile.objects.select_related('user').get(
                    student_id__iexact=identifier,
                    user__is_staff=False,
                    user__is_superuser=False,
                )
            except (StudentProfile.DoesNotExist, StudentProfile.MultipleObjectsReturned):
                pass
            else:
                self.cleaned_data['username'] = student.user.get_username()
        return super().clean()


class StudentPassportWidget(forms.ClearableFileInput):
    template_name = 'portal/widgets/passport_photo.html'


class StudentDetailsForm(forms.ModelForm):
    first_name = forms.CharField(label='First name', max_length=150)
    last_name = forms.CharField(label='Surname', max_length=150)
    email = forms.EmailField(label='Email address', required=False)
    result_pin = forms.RegexField(
        r'^[0-9]{12}$', label='Result-checker PIN', required=False,
        help_text='Optional. Enter the 12 digits from the student’s result card.',
        error_messages={'invalid': 'Enter exactly 12 digits, or leave this blank.'},
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'maxlength': 12}),
    )
    login_password = forms.CharField(
        label='Login password', strip=False,
        help_text='Use at least 8 characters. Avoid names and common passwords.',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'id': 'id_password'}),
    )

    class Meta:
        model = StudentProfile
        fields = (
            'first_name', 'middle_name', 'last_name', 'date_of_birth',
            'student_id', 'current_class', 'email', 'passport_photo',
            'result_pin', 'login_password',
        )
        labels = {'student_id': 'Admission number', 'current_class': 'Class'}
        help_texts = {
            'student_id': 'Use the number on the school record, for example EPM/2026/0042.',
            'passport_photo': 'Optional. Upload a clear passport photograph.',
        }
        widgets = {
            'date_of_birth': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'passport_photo': StudentPassportWidget(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            user = self.instance.user
            for name in ('first_name', 'last_name', 'email'):
                self.initial[name] = getattr(user, name)
            self.fields['login_password'].required = False
            self.fields['login_password'].label = 'New login password'
            self.fields['login_password'].help_text = 'Leave blank to keep the current password. Enter a new password to reset it.'

    def clean_student_id(self):
        admission_number = self.cleaned_data['student_id']
        RegexValidator(
            r'^[\w.@+/-]+\Z',
            'Use letters, numbers, slashes, hyphens, underscores or full stops in the admission number.',
        )(admission_number)
        profiles = StudentProfile.objects.filter(student_id__iexact=admission_number)
        users = get_user_model().objects.filter(username__iexact=admission_number)
        if self.instance.pk:
            profiles = profiles.exclude(pk=self.instance.pk)
            users = users.exclude(pk=self.instance.user_id)
        if profiles.exists() or users.exists():
            raise forms.ValidationError('This admission number is already in use. Check the existing student record.')
        return admission_number

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth and date_of_birth > timezone.localdate():
            raise forms.ValidationError('Date of birth must be today or earlier.')
        return date_of_birth

    def clean_login_password(self):
        password = self.cleaned_data.get('login_password')
        if password:
            user = get_user_model()(
                username=self.instance.user.username if self.instance.pk else self.cleaned_data.get('student_id', ''),
                first_name=self.cleaned_data.get('first_name', ''),
                last_name=self.cleaned_data.get('last_name', ''),
                email=self.cleaned_data.get('email', ''),
            )
            validate_password(password, user)
        return password

    @transaction.atomic
    def save(self):
        if self.instance.pk:
            student = self.instance
            user = student.user
        else:
            user = get_user_model()(username=f'student.{uuid4().hex}')
            student = None
        for name in ('first_name', 'last_name', 'email'):
            setattr(user, name, self.cleaned_data[name])
        if self.cleaned_data.get('login_password'):
            user.set_password(self.cleaned_data['login_password'])
        user.save()
        # Account creation already creates a profile through the existing signal.
        if student is None:
            student = user.studentprofile
        for name in ('middle_name', 'date_of_birth', 'student_id', 'current_class', 'result_pin'):
            setattr(student, name, self.cleaned_data[name])
        photo = self.cleaned_data.get('passport_photo')
        if photo is False:
            student.passport_photo = None
        elif photo:
            student.passport_photo = photo
        student.save()
        self.instance = student
        return student
