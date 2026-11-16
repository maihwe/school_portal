from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.portal_login, name='login'),
    path('logout/', views.portal_logout, name='logout'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('staff/', views.staff_portal, name='staff_portal'),
    path('portal-admin/', views.admin_portal, name='admin_portal'),
    path('portal-admin/students/add/', views.admin_student_details, name='admin_student_add'),
    path('portal-admin/students/<int:student_id>/edit/', views.admin_student_details, name='admin_student_edit'),
    path('media/<path:photo_path>', views.student_photo, name='student_photo'),
    path('payments/demo/<int:invoice_id>/', views.demo_payment, name='demo_payment'),
]
