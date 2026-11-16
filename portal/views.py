from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import PortalAuthenticationForm, StudentDetailsForm
from .models import StudentProfile, ExamResult, SchoolFeeInvoice
from .signals import create_student_profile


def home(request):
    return render(request, 'portal/home.html')


def portal_login(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    form = PortalAuthenticationForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.is_superuser:
            return redirect('admin_portal')
        if user.is_staff:
            return redirect('staff_portal')
        return redirect('student_dashboard')
    return render(request, 'portal/login.html', {'form': form})


def portal_logout(request):
    logout(request)
    return redirect('home')

@login_required
def student_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_portal')
    if request.user.is_staff:
        return redirect('staff_portal')
    # Find the logged-in student's profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        create_student_profile(request.user)
        student_profile = StudentProfile.objects.get(user=request.user)
    
    # Always pull fee invoices
    invoices = SchoolFeeInvoice.objects.filter(student=student_profile)
    unpaid_fees = invoices.filter(is_paid=False)
    total_unpaid = sum(invoice.amount for invoice in unpaid_fees)
    
    results = None
    pin_error = None
    pin_verified = False

    # Check if the student clicked the "Check Result" button
    if request.method == 'POST' and 'verify_pin' in request.POST:
        entered_pin = request.POST.get('result_pin')
        
        # Check if the entered PIN matches the student's assigned PIN
        if student_profile.result_pin and entered_pin == student_profile.result_pin:
            results = ExamResult.objects.filter(student=student_profile)
            pin_verified = True
        else:
            pin_error = "❌ Invalid Result Checker PIN. Please check your scratch card and try again."

    context = {
        'student': student_profile,
        'results': results,
        'invoices': invoices,
        'total_unpaid': total_unpaid,
        'pin_error': pin_error,
        'pin_verified': pin_verified,
    }
    return render(request, 'portal/dashboard.html', context)


@user_passes_test(lambda user: user.is_staff, login_url='login')
def staff_portal(request):
    return render(request, 'portal/staff.html')


@user_passes_test(lambda user: user.is_active and user.is_superuser, login_url='login')
def admin_portal(request):
    students = StudentProfile.objects.filter(user__is_staff=False, user__is_superuser=False).select_related('user')
    student_count = students.count()
    query = request.GET.get('q', '').strip()
    if query:
        students = students.filter(
            Q(student_id__icontains=query) | Q(user__first_name__icontains=query)
            | Q(middle_name__icontains=query) | Q(user__last_name__icontains=query)
        )
    page = Paginator(students.order_by('user__last_name', 'user__first_name', 'pk'), 20).get_page(request.GET.get('page'))
    return render(request, 'portal/admin_portal.html', {
        'students': page, 'student_count': student_count, 'query': query,
    })


@user_passes_test(lambda user: user.is_active and user.is_superuser, login_url='login')
def admin_student_details(request, student_id=None):
    student = None
    if student_id is not None:
        student = get_object_or_404(StudentProfile, pk=student_id, user__is_staff=False, user__is_superuser=False)
    form = StudentDetailsForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
        instance=student,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            saved_student = form.save()
        except IntegrityError:
            form.add_error('student_id', 'These login details are already in use. Check the admission number and try again.')
        else:
            action = 'updated' if student else 'added'
            messages.success(request, f'{saved_student.user.get_full_name()} ({saved_student.student_id}) has been {action}.')
            return redirect('admin_student_edit', student_id=saved_student.pk)
    if student is not None and form.errors:
        student.refresh_from_db()
    return render(request, 'portal/admin_student_form.html', {'form': form, 'student': student})


@login_required
def student_photo(request, photo_path):
    photos = StudentProfile.objects.filter(passport_photo=photo_path)
    if not request.user.is_superuser:
        photos = photos.filter(user=request.user)
    student = get_object_or_404(photos)
    try:
        return FileResponse(student.passport_photo.open('rb'))
    except OSError:
        raise Http404('Photograph not found.')


@login_required
def demo_payment(request, invoice_id):
    if request.method != 'POST':
        return redirect('student_dashboard')
    invoice = get_object_or_404(SchoolFeeInvoice, id=invoice_id, student__user=request.user, is_paid=False)
    invoice.is_paid = True
    invoice.payment_reference = f"EPM-DEMO-{timezone.now():%Y%m%d%H%M%S}-{invoice.id}"
    invoice.save(update_fields=['is_paid', 'payment_reference'])
    messages.success(request, f"Demo payment successful. Reference: {invoice.payment_reference}")
    return redirect('student_dashboard')
