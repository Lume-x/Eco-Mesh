import secrets
from django.contrib import admin
from django.utils import timezone
from .models import MeshNode, UserDataWallet, Voucher, ServiceSchedule, ServiceType, TechnicianProfile


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'estimated_duration_minutes', 'price', 'icon_name', 'badge_color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone_number', 'specialization', 'assigned_zone', 'is_available')
    list_filter = ('is_available', 'assigned_zone')
    search_fields = ('full_name', 'user__username', 'phone_number', 'specialization')


@admin.register(MeshNode)
class MeshNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_area', 'status', 'battery_level', 'signal_quality', 'uptime_percentage', 'next_maintenance_date')
    list_filter = ('status', 'signal_quality')
    search_fields = ('name', 'location_area', 'maintenance_note')
    ordering = ('-status', 'name')
    actions = ['set_nodes_active', 'set_nodes_maintenance']

    @admin.action(description="Set selected nodes to ACTIVE (Operational)")
    def set_nodes_active(self, request, queryset):
        count = queryset.update(status='ACTIVE')
        self.message_user(request, f"Updated {count} node(s) to ACTIVE status.")

    @admin.action(description="Set selected nodes to MAINTENANCE")
    def set_nodes_maintenance(self, request, queryset):
        count = queryset.update(status='MAINTENANCE', next_maintenance_date=timezone.now())
        self.message_user(request, f"Updated {count} node(s) to MAINTENANCE mode.")


@admin.register(UserDataWallet)
class UserDataWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance_mb', 'get_balance_gb', 'wifi_access_key', 'assigned_node')
    search_fields = ('user__username', 'user__email', 'wifi_access_key')
    list_filter = ('assigned_node',)
    raw_id_fields = ('user',)

    @admin.display(description="Balance (GB)")
    def get_balance_gb(self, obj):
        return f"{obj.balance_in_gb} GB"


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'get_amount_gb', 'is_redeemed', 'redeemed_by', 'redeemed_at')
    list_filter = ('is_redeemed',)
    search_fields = ('code', 'redeemed_by__username')
    readonly_fields = ('redeemed_at',)
    actions = ['generate_ten_gb_vouchers', 'generate_twentyfive_gb_vouchers']

    @admin.display(description="Data Amount (GB)")
    def get_amount_gb(self, obj):
        return f"{obj.data_amount_gb} GB"

    @admin.action(description="Generate 5x 10 GB Promotional Vouchers")
    def generate_ten_gb_vouchers(self, request, queryset):
        created_count = 0
        for _ in range(5):
            code = f"ECO-10GB-{secrets.token_hex(3).upper()}"
            if not Voucher.objects.filter(code=code).exists():
                Voucher.objects.create(code=code, data_amount_mb=10240)
                created_count += 1
        self.message_user(request, f"Successfully generated {created_count} promotional 10 GB vouchers.")

    @admin.action(description="Generate 5x 25 GB Promotional Vouchers")
    def generate_twentyfive_gb_vouchers(self, request, queryset):
        created_count = 0
        for _ in range(5):
            code = f"ECO-25GB-{secrets.token_hex(3).upper()}"
            if not Voucher.objects.filter(code=code).exists():
                Voucher.objects.create(code=code, data_amount_mb=25600)
                created_count += 1
        self.message_user(request, f"Successfully generated {created_count} promotional 25 GB vouchers.")


@admin.register(ServiceSchedule)
class ServiceScheduleAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'service_type', 'node', 'technician', 'scheduled_date', 'scheduled_time', 'status', 'created_at')
    list_filter = ('status', 'service_type', 'scheduled_date', 'technician')
    search_fields = ('user__username', 'address', 'notes', 'node__name', 'technician_notes')
    actions = ['mark_confirmed', 'mark_in_progress', 'mark_completed', 'mark_cancelled']

    @admin.action(description="Mark selected appointments as CONFIRMED")
    def mark_confirmed(self, request, queryset):
        count = queryset.update(status='CONFIRMED')
        self.message_user(request, f"Marked {count} appointment(s) as Confirmed.")

    @admin.action(description="Mark selected appointments as IN PROGRESS")
    def mark_in_progress(self, request, queryset):
        count = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"Marked {count} appointment(s) as In Progress.")

    @admin.action(description="Mark selected appointments as COMPLETED")
    def mark_completed(self, request, queryset):
        count = queryset.update(status='COMPLETED')
        self.message_user(request, f"Marked {count} appointment(s) as Completed.")

    @admin.action(description="Mark selected appointments as CANCELLED")
    def mark_cancelled(self, request, queryset):
        count = queryset.update(status='CANCELLED')
        self.message_user(request, f"Marked {count} appointment(s) as Cancelled.")
