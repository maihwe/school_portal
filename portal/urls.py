from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.portal_login, name='login'),
    path('logout/', views.portal_logout, name='logout'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('staff/', views.staff_portal, name='staff_portal'),
    path('portal-admin/', views.admin_portal, name='admin_portal'),
    path('payments/demo/<int:invoice_id>/', views.demo_payment, name='demo_payment'),
]
