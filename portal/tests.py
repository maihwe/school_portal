import io
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import StudentProfile


class PortalLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'Student-test-password!'
        cls.student = get_user_model().objects.create_user(
            username='test.student', password=cls.password,
        )
        cls.profile = cls.student.studentprofile
        cls.profile.student_id = 'EPM/2026/0042'
        cls.profile.result_pin = '123456789012'
        cls.profile.save()

    def sign_in(self, identifier, password=None):
        return self.client.post(reverse('login'), {
            'username': identifier,
            'password': self.password if password is None else password,
        })

    def test_student_can_use_username_or_admission_number(self):
        for identifier in ['test.student', 'EPM/2026/0042', ' epm/2026/0042 ']:
            with self.subTest(identifier=identifier):
                self.client.logout()
                response = self.sign_in(identifier)
                self.assertRedirects(response, reverse('student_dashboard'))
                self.assertEqual(self.client.session['_auth_user_id'], str(self.student.pk))

    def test_failed_login_keeps_identifier_but_never_password(self):
        response = self.sign_in('EPM/2026/0042', 'Wrong-password!')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="EPM/2026/0042"')
        self.assertContains(response, "We couldn't sign you in.")
        self.assertNotContains(response, 'Wrong-password!')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unknown_identifier_has_same_error_as_wrong_password(self):
        unknown = self.sign_in('EPM/2026/9999')
        wrong_password = self.sign_in('EPM/2026/0042', 'Wrong-password!')
        self.assertContains(unknown, "We couldn't sign you in.")
        self.assertEqual(
            unknown.context['form'].non_field_errors(),
            wrong_password.context['form'].non_field_errors(),
        )
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_result_pin_does_not_replace_password(self):
        response = self.sign_in('EPM/2026/0042', self.profile.result_pin)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_inactive_student_cannot_log_in(self):
        self.student.is_active = False
        self.student.save(update_fields=['is_active'])
        response = self.sign_in(self.profile.student_id)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_staff_and_admin_keep_their_own_destinations(self):
        for username, is_superuser, destination in [
            ('test.staff', False, 'staff_portal'),
            ('test.admin', True, 'admin_portal'),
        ]:
            with self.subTest(username=username):
                self.client.logout()
                get_user_model().objects.create_user(
                    username=username, password=self.password,
                    is_staff=True, is_superuser=is_superuser,
                )
                self.assertRedirects(self.sign_in(username), reverse(destination))

    def test_existing_username_takes_precedence_over_admission_number(self):
        other = get_user_model().objects.create_user(
            username=self.profile.student_id, password='Other-password!',
        )
        self.assertEqual(self.sign_in(self.profile.student_id).status_code, 200)
        response = self.sign_in(self.profile.student_id, 'Other-password!')
        self.assertRedirects(response, reverse('student_dashboard'))
        self.assertEqual(self.client.session['_auth_user_id'], str(other.pk))

    def test_ambiguous_admission_number_cannot_log_in(self):
        other = get_user_model().objects.create_user(username='other.student', password=self.password)
        StudentProfile.objects.filter(user=other).update(student_id='epm/2026/0042')
        response = self.sign_in(self.profile.student_id)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_empty_submission_has_errors(self):
        response = self.client.post(reverse('login'), {})
        self.assertTrue(response.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_requires_csrf_token(self):
        client = self.client_class(enforce_csrf_checks=True)
        response = client.post(reverse('login'), {
            'username': self.profile.student_id, 'password': self.password,
        })
        self.assertEqual(response.status_code, 403)


class StudentManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username='record.admin', password='Admin-test-password!',
        )
        cls.student_user = get_user_model().objects.create_user(
            username='existing.student', first_name='Amaka', last_name='Peter',
            password='Existing-test-password!',
        )
        cls.student = cls.student_user.studentprofile
        cls.student.student_id = 'EPM/2026/0042'
        cls.student.save()
        # Older records can include a student profile for an administrator.
        StudentProfile.objects.create(user=cls.admin, student_id='ADMIN-OLD', current_class='JSS 1')

    def setUp(self):
        self.client.force_login(self.admin)
        self.data = {
            'first_name': 'David', 'middle_name': 'John', 'last_name': 'Okoh',
            'date_of_birth': '2012-04-18', 'student_id': 'EPM/2026/0050',
            'current_class': 'JSS 2', 'email': 'david@example.com',
            'result_pin': '123456789012', 'login_password': 'School-login-test!',
        }

    def test_add_creates_one_profile_and_a_working_student_login(self):
        response = self.client.post(reverse('admin_student_add'), self.data)
        student = StudentProfile.objects.get(student_id=self.data['student_id'])
        self.assertRedirects(response, reverse('admin_student_edit', args=[student.pk]))
        self.assertEqual(StudentProfile.objects.filter(user=student.user).count(), 1)
        self.assertEqual(student.user.first_name, 'David')
        self.assertEqual(student.middle_name, 'John')
        self.assertEqual(student.current_class, 'JSS 2')
        self.assertEqual(student.date_of_birth.isoformat(), '2012-04-18')
        self.assertEqual(student.user.email, 'david@example.com')
        self.assertFalse(student.user.is_staff)
        self.assertFalse(student.user.is_superuser)
        self.assertTrue(student.user.check_password(self.data['login_password']))
        self.client.logout()
        login = self.client.post(reverse('login'), {
            'username': student.student_id, 'password': self.data['login_password'],
        })
        self.assertRedirects(login, reverse('student_dashboard'))

    def test_edit_keeps_account_and_password_when_new_password_is_blank(self):
        self.data['student_id'] = self.student.student_id
        self.data['login_password'] = ''
        user_count = get_user_model().objects.count()
        response = self.client.post(reverse('admin_student_edit', args=[self.student.pk]), self.data)
        self.assertRedirects(response, reverse('admin_student_edit', args=[self.student.pk]))
        self.student.refresh_from_db()
        self.student_user.refresh_from_db()
        self.assertEqual(get_user_model().objects.count(), user_count)
        self.assertEqual(self.student.user_id, self.student_user.pk)
        self.assertEqual(self.student_user.username, 'existing.student')
        self.assertEqual(self.student_user.first_name, 'David')
        self.assertTrue(self.student_user.check_password('Existing-test-password!'))

    def test_admin_can_reset_student_password(self):
        self.data['student_id'] = self.student.student_id
        response = self.client.post(reverse('admin_student_edit', args=[self.student.pk]), self.data)
        self.assertEqual(response.status_code, 302)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password(self.data['login_password']))
        self.assertFalse(self.student_user.check_password('Existing-test-password!'))

    def test_validation_preserves_details_without_creating_accounts(self):
        count = get_user_model().objects.count()
        for changes, error_field in [
            ({'student_id': 'epm/2026/0042'}, 'student_id'),
            ({'student_id': self.admin.username}, 'student_id'),
            ({'result_pin': '1234'}, 'result_pin'),
            ({'login_password': '123'}, 'login_password'),
            ({'login_password': ''}, 'login_password'),
            ({'first_name': ''}, 'first_name'),
            ({'current_class': 'Unknown class'}, 'current_class'),
            ({'date_of_birth': (timezone.localdate() + timedelta(days=1)).isoformat()}, 'date_of_birth'),
        ]:
            with self.subTest(error_field=error_field, changes=changes):
                response = self.client.post(reverse('admin_student_add'), {**self.data, **changes})
                self.assertEqual(response.status_code, 200)
                self.assertIn(error_field, response.context['form'].errors)
                self.assertContains(response, 'value="Okoh"')
                self.assertNotContains(response, self.data['login_password'])
                self.assertEqual(get_user_model().objects.count(), count)

    def test_optional_details_can_be_left_blank(self):
        self.data.update(middle_name='', date_of_birth='', email='', result_pin='')
        response = self.client.post(reverse('admin_student_add'), self.data)
        self.assertEqual(response.status_code, 302)
        student = StudentProfile.objects.get(student_id=self.data['student_id'])
        self.assertIsNone(student.date_of_birth)
        self.assertEqual(student.result_pin, '')

    def test_account_and_profile_changes_roll_back_on_database_failure(self):
        user_count = get_user_model().objects.count()
        with patch('portal.forms.StudentProfile.save', side_effect=IntegrityError('Synthetic conflict')):
            response = self.client.post(reverse('admin_student_add'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), user_count)
        self.assertFalse(StudentProfile.objects.filter(student_id=self.data['student_id']).exists())
        self.assertIn('student_id', response.context['form'].errors)

    def test_student_and_staff_cannot_add_or_edit_student_records(self):
        staff = get_user_model().objects.create_user(username='record.staff', is_staff=True)
        before = get_user_model().objects.count()
        for user in [self.student_user, staff, None]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            for url in [reverse('admin_student_add'), reverse('admin_student_edit', args=[self.student.pk])]:
                with self.subTest(user=user, url=url):
                    response = self.client.post(url, self.data)
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith(reverse('login')))
        self.assertEqual(get_user_model().objects.count(), before)
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.first_name, 'Amaka')

    def test_administrator_profiles_are_not_editable_as_students(self):
        profile = self.admin.studentprofile
        response = self.client.post(reverse('admin_student_edit', args=[profile.pk]), self.data)
        self.assertEqual(response.status_code, 404)

    def test_list_shows_real_students_and_searches_names_and_numbers(self):
        response = self.client.get(reverse('admin_portal'))
        self.assertEqual(response.context['student_count'], 1)
        self.assertContains(response, self.student.student_id)
        self.assertNotContains(response, 'ADMIN-OLD')
        for query in ['Amaka', 'Peter', '2026/0042']:
            response = self.client.get(reverse('admin_portal'), {'q': query})
            self.assertEqual(response.context['students'].paginator.count, 1)
        response = self.client.get(reverse('admin_portal'), {'q': 'Missing student'})
        self.assertContains(response, 'No students match your search.')

    def test_student_list_is_paginated(self):
        for index in range(21):
            get_user_model().objects.create_user(username=f'page.student.{index}')
        response = self.client.get(reverse('admin_portal'), {'page': '2'})
        self.assertEqual(response.context['students'].number, 2)
        self.assertEqual(len(response.context['students']), 2)
        self.assertContains(response, 'Previous')

    def test_photograph_upload_is_viewable_only_by_admin_and_its_student(self):
        image_data = io.BytesIO()
        Image.new('RGB', (8, 8), 'green').save(image_data, format='PNG')
        upload = SimpleUploadedFile('passport.png', image_data.getvalue(), content_type='image/png')
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(reverse('admin_student_add'), {**self.data, 'passport_photo': upload})
            self.assertEqual(response.status_code, 302)
            student = StudentProfile.objects.get(student_id=self.data['student_id'])
            photo_url = student.passport_photo.url
            response = self.client.get(photo_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), image_data.getvalue())
            self.client.force_login(self.student_user)
            self.assertEqual(self.client.get(photo_url).status_code, 404)
            self.client.force_login(student.user)
            response = self.client.get(photo_url)
            self.assertEqual(response.status_code, 200)
            response.close()
            self.client.logout()
            self.assertEqual(self.client.get(photo_url).status_code, 302)
            self.client.force_login(self.admin)
            edit_url = reverse('admin_student_edit', args=[student.pk])
            edit_data = {**self.data, 'login_password': ''}
            self.assertEqual(self.client.post(edit_url, edit_data).status_code, 302)
            student.refresh_from_db()
            self.assertEqual(student.passport_photo.url, photo_url)
            self.assertEqual(self.client.post(edit_url, {**edit_data, 'passport_photo-clear': 'on'}).status_code, 302)
            student.refresh_from_db()
            self.assertFalse(student.passport_photo)
            self.assertEqual(self.client.get(photo_url).status_code, 404)

    def test_student_creation_requires_csrf_token(self):
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(reverse('admin_student_add'), self.data)
        self.assertEqual(response.status_code, 403)
