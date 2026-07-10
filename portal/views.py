from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, ExamResult, SchoolFeeInvoice

@login_required
def student_dashboard(request):
    # Find the logged-in student's profile
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return render(request, 'portal/error.html', {'message': 'No student profile found.'})
    
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
