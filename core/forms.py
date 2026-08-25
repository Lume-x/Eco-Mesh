from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import ServiceSchedule, Voucher, MeshNode, UserDataWallet, ServiceType, TechnicianProfile


TIME_SLOT_CHOICES = [
    ('09:00:00', '09:00 AM (Morning Slot 1)'),
    ('10:30:00', '10:30 AM (Morning Slot 2)'),
    ('12:00:00', '12:00 PM (Midday Slot)'),
    ('14:00:00', '02:00 PM (Afternoon Slot 1)'),
    ('15:30:00', '03:30 PM (Afternoon Slot 2)'),
    ('17:00:00', '05:00 PM (Evening Slot)'),
]

INPUT_CLASS = 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-500/25 transition duration-200 text-sm shadow-inner'
SELECT_CLASS = 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-500/25 transition duration-200 text-sm shadow-inner'
TEXTAREA_CLASS = 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-500/25 transition duration-200 text-sm shadow-inner'


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Create a secure password (min 6 chars)'
        }),
        min_length=6,
        help_text="Must be at least 6 characters"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Confirm your password'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'student@university.edu or email@domain.com'
        })
    )
    assigned_node = forms.ModelChoiceField(
        queryset=MeshNode.objects.filter(status='ACTIVE'),
        required=False,
        empty_label="Auto-assign nearest operational node",
        widget=forms.Select(attrs={
            'class': SELECT_CLASS
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Choose a unique username'
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            assigned_node = self.cleaned_data.get('assigned_node')
            if not assigned_node:
                assigned_node = MeshNode.objects.filter(status='ACTIVE').first()
            
            # 500 MB welcome grant for new student registration
            UserDataWallet.objects.get_or_create(
                user=user,
                defaults={'balance_mb': 500, 'assigned_node': assigned_node}
            )
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Enter your password'
        })
    )


class VoucherRedeemForm(forms.Form):
    code = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS + ' font-mono uppercase tracking-wider',
            'placeholder': 'e.g. ECO-10GB-XYZ123'
        }),
        help_text="Enter your 16-character scratch card voucher or promotional code."
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError("Please enter a voucher code.")
        return code


class ServiceScheduleForm(forms.ModelForm):
    scheduled_time = forms.ChoiceField(
        choices=TIME_SLOT_CHOICES,
        widget=forms.Select(attrs={
            'class': SELECT_CLASS + ' font-mono'
        }),
        help_text="Choose from our standard 90-minute field dispatch slots."
    )

    class Meta:
        model = ServiceSchedule
        fields = ['service_type', 'node', 'address', 'scheduled_date', 'scheduled_time', 'notes']
        widgets = {
            'service_type': forms.Select(attrs={
                'class': SELECT_CLASS
            }),
            'node': forms.Select(attrs={
                'class': SELECT_CLASS
            }),
            'address': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'e.g. Room 304, Hostel B Annex, South Campus'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'class': INPUT_CLASS + ' font-mono'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': TEXTAREA_CLASS,
                'placeholder': 'Provide any helpful context (e.g. weak Wi-Fi in room corner, 3rd floor balcony access, inverter blinking red).'
            }),
        }

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.localdate():
            raise ValidationError("Service appointments cannot be scheduled in the past.")
        return scheduled_date


class TechnicianStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = ServiceSchedule
        fields = ['status', 'technician_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': SELECT_CLASS
            }),
            'technician_notes': forms.Textarea(attrs={
                'rows': 3,
                'class': TEXTAREA_CLASS,
                'placeholder': 'Log work summary, antenna alignment readings (RSSI/SNR), or hardware replacement details.'
            })
        }


class AdminAssignTechnicianForm(forms.ModelForm):
    technician = forms.ModelChoiceField(
        queryset=User.objects.filter(technician_profile__isnull=False),
        required=False,
        empty_label="-- Unassigned (Assign Later) --",
        widget=forms.Select(attrs={
            'class': SELECT_CLASS + ' text-xs py-1.5'
        })
    )

    class Meta:
        model = ServiceSchedule
        fields = ['technician', 'status']
        widgets = {
            'status': forms.Select(attrs={
                'class': SELECT_CLASS + ' text-xs py-1.5'
            })
        }


class AdminServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'code', 'description', 'estimated_duration_minutes', 'price', 'icon_name', 'badge_color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'code': forms.TextInput(attrs={'class': INPUT_CLASS + ' uppercase font-mono'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': TEXTAREA_CLASS}),
            'estimated_duration_minutes': forms.NumberInput(attrs={'class': INPUT_CLASS}),
            'price': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'icon_name': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'badge_color': forms.TextInput(attrs={'class': INPUT_CLASS}),
        }


class AdminGenerateVoucherForm(forms.Form):
    data_amount_mb = forms.IntegerField(
        min_value=100,
        initial=1024,
        widget=forms.NumberInput(attrs={
            'class': INPUT_CLASS + ' font-mono',
            'placeholder': 'Amount in MB (e.g. 1024, 5120, 10240, 61440)'
        }),
        help_text="1 GB = 1024 MB, 5 GB = 5120 MB, 10 GB = 10240 MB, 60 GB = 61440 MB"
    )
    custom_code = forms.CharField(
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASS + ' font-mono uppercase',
            'placeholder': 'e.g. PROMO-FUTO-5GB (Optional)'
        }),
        help_text="Optional custom alphanumeric code. Leave blank to auto-generate."
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': INPUT_CLASS,
            'placeholder': 'Quantity of vouchers to generate (1-100)'
        })
    )


class AdminMeshNodeForm(forms.ModelForm):
    class Meta:
        model = MeshNode
        fields = ['name', 'location_area', 'battery_level', 'status', 'signal_quality', 'uptime_percentage', 'next_maintenance_date', 'maintenance_note']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Node Name (e.g. Hostel B - Rooftop Relay)'
            }),
            'location_area': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Location Area (e.g. Campus Zone)'
            }),
            'battery_level': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min': 0,
                'max': 100,
                'placeholder': 'Battery Charge % (0-100)'
            }),
            'status': forms.Select(attrs={
                'class': SELECT_CLASS
            }),
            'signal_quality': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Optimal / Good / Fair'
            }),
            'uptime_percentage': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'step': '0.1',
                'min': 0,
                'max': 100,
                'placeholder': '99.8'
            }),
            'next_maintenance_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': INPUT_CLASS + ' font-mono'
            }),
            'maintenance_note': forms.Textarea(attrs={
                'rows': 2,
                'class': TEXTAREA_CLASS,
                'placeholder': 'Field engineer notes on solar array, antenna alignment, or battery telemetry.'
            }),
        }
