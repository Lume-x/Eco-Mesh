from django.urls import path
from . import views

urlpatterns = [
    # Public pages & Scheduling Home
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('team/', views.team_view, name='team'),
    path('pricing/', views.pricing_view, name='pricing'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Client Dashboard & Scheduling
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('book-service/', views.book_service_view, name='book_service'),
    path('booking-confirmation/<int:schedule_id>/', views.booking_confirmation_view, name='booking_confirmation'),
    path('cancel-service/<int:schedule_id>/', views.cancel_service_view, name='cancel_service'),
    path('redeem-voucher/', views.redeem_voucher_view, name='redeem_voucher'),

    # Technician Portal
    path('technician/portal/', views.technician_portal_view, name='technician_portal'),
    path('technician/update-status/<int:schedule_id>/', views.technician_update_status_view, name='technician_update_status'),

    # Admin Scheduling & Node Infrastructure Command Centers
    path('admin-scheduling/', views.admin_scheduling_dashboard_view, name='admin_scheduling'),
    path('admin-generate-voucher/', views.admin_generate_voucher_view, name='admin_generate_voucher'),
    path('admin-create-node/', views.admin_create_node_view, name='admin_create_node'),
    path('admin-update-node/<int:node_id>/', views.admin_update_node_view, name='admin_update_node'),
    path('admin-delete-node/<int:node_id>/', views.admin_delete_node_view, name='admin_delete_node'),

    # Real-Time Availability API
    path('api/check-availability/', views.api_check_availability, name='api_check_availability'),
]
