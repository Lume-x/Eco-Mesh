from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('team/', views.team_view, name='team'),
    path('pricing/', views.pricing_view, name='pricing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('redeem-voucher/', views.redeem_voucher_view, name='redeem_voucher'),
    path('admin-generate-voucher/', views.admin_generate_voucher_view, name='admin_generate_voucher'),
    path('admin-create-node/', views.admin_create_node_view, name='admin_create_node'),
    path('admin-update-node/<int:node_id>/', views.admin_update_node_view, name='admin_update_node'),
    path('admin-delete-node/<int:node_id>/', views.admin_delete_node_view, name='admin_delete_node'),
    path('book-service/', views.book_service_view, name='book_service'),
    path('cancel-service/<int:schedule_id>/', views.cancel_service_view, name='cancel_service'),
]
