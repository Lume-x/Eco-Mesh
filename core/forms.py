from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import ServiceSchedule, Voucher, MeshNode, UserDataWallet


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'Create a secure password (min 6 chars)'
        }),
        min_length=6,
        help_text="Must be at least 6 characters"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'Confirm your password'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'student@university.edu or email@domain.com'
        })
    )
    assigned_node = forms.ModelChoiceField(
        queryset=MeshNode.objects.filter(status='ACTIVE'),
        required=False,
        empty_label="Auto-assign nearest operational node",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
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
            # Initialize UserDataWallet with optional assigned node
            assigned_node = self.cleaned_data.get('assigned_node')
            if not assigned_node:
                assigned_node = MeshNode.objects.filter(status='ACTIVE').first()
            
            # Start new student users with 500 MB welcome grant
            UserDataWallet.objects.get_or_create(
                user=user,
                defaults={'balance_mb': 500, 'assigned_node': assigned_node}
            )
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'Your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'Your password'
        })
    )


class VoucherRedeemForm(forms.Form):
    code = forms.CharField(
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'w-full uppercase font-mono tracking-widest px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-emerald-400 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
            'placeholder': 'e.g. ECO-10GB-SUN'
        }),
        help_text="Enter the 12-16 character code printed on your EcoMesh scratch card."
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError("Please enter a voucher code.")
        return code


class ServiceScheduleForm(forms.ModelForm):
    class Meta:
        model = ServiceSchedule
        fields = ['service_type', 'node', 'address', 'scheduled_date', 'scheduled_time', 'notes']
        widgets = {
            'service_type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200'
            }),
            'node': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
                'placeholder': 'e.g. Room 402, Sunshine Hostel, South Campus'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200'
            }),
            'scheduled_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition duration-200',
                'placeholder': 'Provide any helpful context for the technician (e.g. 3rd floor rooftop access, weak signal in back bedroom).'
            }),
        }

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.localdate():
            raise ValidationError("Appointments cannot be scheduled in the past.")
        return scheduled_date


class AdminGenerateVoucherForm(forms.Form):
    data_amount_mb = forms.IntegerField(
        min_value=100,
        initial=1024,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition font-mono',
            'placeholder': 'Amount in MB (e.g. 1024, 5120, 10240, 61440)'
        }),
        help_text="1 GB = 1024 MB, 5 GB = 5120 MB, 10 GB = 10240 MB, 60 GB = 61440 MB"
    )
    custom_code = forms.CharField(
        required=False,
        max_length=32,
        widget=forms.TextInput(attrs={
            'class': 'w-full uppercase font-mono tracking-wider px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-emerald-400 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition',
            'placeholder': 'Optional custom code (e.g. SPECIAL-PROMO-10GB)'
        }),
        help_text="Leave blank to auto-generate a secure randomized promo code."
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition font-mono',
            'placeholder': 'Quantity (1-100)'
        })
    )

    def clean_custom_code(self):
        code = self.cleaned_data.get('custom_code', '').strip().upper()
        if code and Voucher.objects.filter(code=code).exists():
            raise ValidationError(f"A promo voucher with code '{code}' already exists.")
        return code


class AdminMeshNodeForm(forms.ModelForm):
    class Meta:
        model = MeshNode
        fields = ['name', 'location_area', 'battery_level', 'status', 'signal_quality', 'uptime_percentage', 'next_maintenance_date', 'maintenance_note']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition',
                'placeholder': 'e.g. Hall 4 Rooftop Node'
            }),
            'location_area': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition',
                'placeholder': 'Campus Zone'
            }),
            'battery_level': forms.NumberInput(attrs={
                'min': '0',
                'max': '100',
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition font-mono'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition'
            }),
            'signal_quality': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition'
            }),
            'uptime_percentage': forms.NumberInput(attrs={
                'step': '0.1',
                'min': '0',
                'max': '100',
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition font-mono'
            }),
            'next_maintenance_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition'
            }),
            'maintenance_note': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition',
                'placeholder': 'e.g. Scheduled battery upgrade or solar realigning note'
            }),
        }
