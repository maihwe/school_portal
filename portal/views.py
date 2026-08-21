from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import StudentProfile, ExamResult, SchoolFeeInvoice
from .signals import create_student_profile


def home(request):
    return render(request, 'portal/home.html')


def portal_login(request):
    if request.user.is_authenticated:
        return redirect('student_dashboard')
    form = AuthenticationForm(request, data=request.POST or None)
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


@user_passes_test(lambda user: user.is_superuser, login_url='login')
def admin_portal(request):
    return render(request, 'portal/admin_portal.html')


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
