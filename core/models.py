import secrets
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class MeshNode(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Operational'),
        ('MAINTENANCE', 'Scheduled Maintenance'),
        ('OFFLINE', 'Downtime'),
    ]

    SIGNAL_CHOICES = [
        ('Optimal', 'Optimal (5.8 GHz - 900 Mbps)'),
        ('Good', 'Good (5.8 GHz - 650 Mbps)'),
        ('Fair', 'Fair (2.4 GHz - 300 Mbps)'),
        ('Weak', 'Weak (Mesh Edge - 100 Mbps)'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Unique Node Identifier (e.g., Hostel Block C - Alpha)")
    location_area = models.CharField(max_length=150, help_text="Geographical or campus zone (e.g., Campus South Gate)")
    battery_level = models.PositiveIntegerField(default=100, help_text="Solar LiFePO4 battery charge percentage (0-100%)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    signal_quality = models.CharField(max_length=50, choices=SIGNAL_CHOICES, default='Optimal')
    uptime_percentage = models.FloatField(default=99.8, help_text="Historical 30-day uptime SLA percentage")
    next_maintenance_date = models.DateTimeField(null=True, blank=True, help_text="Next scheduled maintenance or battery servicing window")
    maintenance_note = models.CharField(max_length=255, blank=True, help_text="Brief engineer note regarding upcoming or current maintenance")

    class Meta:
        ordering = ['-status', 'name']
        verbose_name = "Mesh Node"
        verbose_name_plural = "Mesh Nodes"

    def __str__(self):
        return f"{self.name} ({self.location_area}) - {self.get_status_display()}"

    @property
    def is_operational(self):
        return self.status == 'ACTIVE'

    @property
    def battery_status_color(self):
        if self.battery_level >= 70:
            return "emerald"
        elif self.battery_level >= 35:
            return "amber"
        return "rose"


class UserDataWallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance_mb = models.PositiveIntegerField(default=0, help_text="Lifetime perpetual data balance in Megabytes (never expires)")
    wifi_access_key = models.CharField(max_length=16, unique=True, blank=True, help_text="Unique 8-character uppercase hex PIN for WPA3-Enterprise portal authentication")
    assigned_node = models.ForeignKey(MeshNode, null=True, blank=True, on_delete=models.SET_NULL, related_name='connected_users', help_text="Primary connected solar mesh node")

    class Meta:
        verbose_name = "User Data Wallet"
        verbose_name_plural = "User Data Wallets"

    def __str__(self):
        return f"{self.user.username}'s Data Wallet ({self.balance_in_gb} GB)"

    @property
    def balance_in_gb(self):
        return round(self.balance_mb / 1024.0, 2)

    def save(self, *args, **kwargs):
        if not self.wifi_access_key:
            # Generate a secure 8-character uppercase hex key
            while True:
                candidate = secrets.token_hex(4).upper()
                if not UserDataWallet.objects.filter(wifi_access_key=candidate).exists():
                    self.wifi_access_key = candidate
                    break
        super().save(*args, **kwargs)


class Voucher(models.Model):
    code = models.CharField(max_length=32, unique=True, help_text="Unique voucher code (e.g. ECO-10GB-SUN)")
    data_amount_mb = models.PositiveIntegerField(help_text="Data allocation in Megabytes")
    is_redeemed = models.BooleanField(default=False)
    redeemed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='redeemed_vouchers')
    redeemed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_redeemed', '-data_amount_mb']
        verbose_name = "Data Voucher"
        verbose_name_plural = "Data Vouchers"

    def __str__(self):
        status = f"Redeemed by {self.redeemed_by.username}" if self.is_redeemed and self.redeemed_by else "Unredeemed"
        return f"{self.code} [{self.data_amount_gb} GB] - {status}"

    @property
    def data_amount_gb(self):
        return round(self.data_amount_mb / 1024.0, 2)

    def redeem(self, user):
        """Atomically credit data to user wallet and mark voucher as redeemed."""
        if self.is_redeemed:
            raise ValidationError("This voucher has already been redeemed.")
        
        wallet, _ = UserDataWallet.objects.get_or_create(user=user)
        wallet.balance_mb += self.data_amount_mb
        wallet.save()

        self.is_redeemed = True
        self.redeemed_by = user
        self.redeemed_at = timezone.now()
        self.save()
        return wallet


class ServiceSchedule(models.Model):
    SERVICE_TYPES = [
        ('INSTALL', 'New Node Setup / Antenna Mounting'),
        ('REALIGN', 'Signal Alignment / Range Boost'),
        ('REPAIR', 'Solar / Battery / Hardware Servicing'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Technician Review'),
        ('CONFIRMED', 'Confirmed & Dispatched'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="schedules")
    node = models.ForeignKey(MeshNode, null=True, blank=True, on_delete=models.SET_NULL, related_name="service_schedules", help_text="Associated or nearest mesh node")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='INSTALL')
    address = models.CharField(max_length=255, help_text="Hostel, room number, or street address")
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text="Specific instructions or issue description for field engineer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        verbose_name = "Service Schedule"
        verbose_name_plural = "Service Schedules"

    def __str__(self):
        return f"{self.get_service_type_display()} for {self.user.username} on {self.scheduled_date} at {self.scheduled_time}"

    def clean(self):
        super().clean()
        # Validation: prevent duplicate active bookings for the exact same node/date/time slot
        if self.node and self.scheduled_date and self.scheduled_time:
            conflicts = ServiceSchedule.objects.filter(
                node=self.node,
                scheduled_date=self.scheduled_date,
                scheduled_time=self.scheduled_time,
                status__in=['PENDING', 'CONFIRMED']
            )
            if self.pk:
                conflicts = conflicts.exclude(pk=self.pk)
            
            if conflicts.exists():
                raise ValidationError({
                    'scheduled_time': f"A technician appointment is already scheduled for '{self.node.name}' on {self.scheduled_date} at {self.scheduled_time.strftime('%H:%M')}. Please choose another time or date."
                })
