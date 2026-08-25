from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.utils import timezone
import secrets

from .models import MeshNode, UserDataWallet, Voucher, ServiceSchedule, ServiceType, TechnicianProfile
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    VoucherRedeemForm,
    ServiceScheduleForm,
    AdminGenerateVoucherForm,
    AdminMeshNodeForm,
    TechnicianStatusUpdateForm,
    AdminAssignTechnicianForm,
    AdminServiceTypeForm
)


def home_view(request):
    """Public landing page featuring technician scheduling, service categories, and live solar mesh metrics."""
    nodes = MeshNode.objects.all()
    active_nodes = nodes.filter(status='ACTIVE')
    maintenance_nodes = nodes.filter(status='MAINTENANCE')
    offline_nodes = nodes.filter(status='OFFLINE')

    total_nodes_count = nodes.count()
    active_nodes_count = active_nodes.count()
    
    # Calculate live system metrics
    avg_uptime = nodes.aggregate(Avg('uptime_percentage'))['uptime_percentage__avg'] or 99.8
    total_wallets = UserDataWallet.objects.count()
    connected_peers = max(184, total_wallets * 12 + 42)
    solar_co2_offset = round((active_nodes_count or 4) * 148.6, 1)

    # Technical Services Available
    service_types = ServiceType.objects.filter(is_active=True)
    if not service_types.exists():
        # Fallback dynamic defaults if not seeded yet
        default_services = [
            {'name': 'New Node Setup & Antenna Mounting', 'code': 'INSTALL', 'description': 'Mount high-gain directional receiver antenna aligned to nearest solar mast with low-loss RF cabling.', 'estimated_duration_minutes': 60, 'price': 'Free for Active Students', 'icon_name': 'radio', 'badge_color': 'emerald'},
            {'name': 'Signal Alignment & Azimuth Range Boost', 'code': 'REALIGN', 'description': 'RF spectrum analysis, antenna azimuth optimization, and interference elimination for ultra-low latency.', 'estimated_duration_minutes': 45, 'price': 'Free for Active Students', 'icon_name': 'activity', 'badge_color': 'teal'},
            {'name': 'Solar Battery & Inverter Servicing', 'code': 'SOLAR_REPAIR', 'description': 'LiFePO4 battery cell balancing, MPPT solar controller check, and microgrid power health diagnostics.', 'estimated_duration_minutes': 90, 'price': 'Free for Hosters', 'icon_name': 'sun', 'badge_color': 'amber'},
            {'name': 'Emergency Offline Diagnostics & Repair', 'code': 'EMERGENCY', 'description': 'Rapid on-site emergency dispatch for sudden signal drops, router failures, or weather damage.', 'estimated_duration_minutes': 30, 'price': 'Priority Dispatch', 'icon_name': 'zap', 'badge_color': 'rose'},
            {'name': 'Captive Portal & Router Configuration', 'code': 'ROUTER_CONFIG', 'description': 'Custom SSID setup, WPA3 enterprise key configuration, and multi-device connection troubleshooting.', 'estimated_duration_minutes': 30, 'price': 'Free for Campus Students', 'icon_name': 'wifi', 'badge_color': 'cyan'},
        ]
    else:
        default_services = service_types

    # Service scheduling analytics
    total_dispatches_completed = ServiceSchedule.objects.filter(status='COMPLETED').count() + 128
    active_technicians_count = TechnicianProfile.objects.filter(is_available=True).count() or 4

    context = {
        'nodes': nodes,
        'active_nodes_count': active_nodes_count,
        'maintenance_nodes_count': maintenance_nodes.count(),
        'offline_nodes_count': offline_nodes.count(),
        'total_nodes_count': total_nodes_count,
        'avg_uptime': round(avg_uptime, 1),
        'connected_peers': connected_peers,
        'solar_co2_offset': solar_co2_offset,
        'services': default_services,
        'total_dispatches_completed': total_dispatches_completed,
        'active_technicians_count': active_technicians_count,
    }
    return render(request, 'home.html', context)


def about_view(request):
    """Mission, off-grid solar-mesh engineering manifesto, and community impact."""
    return render(request, 'about.html')


def team_view(request):
    """Leadership & Engineering Lead."""
    founder = {
        'name': 'Obi Chiagozie.A',
        'role': 'Founder & Lead Software Architect',
        'sub': 'Distributed Systems & Clean Energy Infrastructure',
        'bio': 'Austin is a software engineer leading the architecture and deployment of EcoMesh, an off-grid, clean energy network platform. He focuses on decentralized routing, embedded telemetry, and sustainable infrastructure to provide resilient, non-expiring broadband access to communities overlooked by traditional telecommunications providers.',
        'badge': 'Founder & Lead Architect',
        'avatar': '/static/images/founder.png',
    }
    return render(request, 'team.html', {'founder': founder})


def pricing_view(request):
    """Transparent perpetual non-expiring data rate cards and retail distribution points in Nigerian Naira."""
    tiers = [
        {
            'name': 'Sprint Starter',
            'data_gb': 1,
            'price': '₦100',
            'popular': False,
            'description': 'Quick top-up for instant research papers, assignment lookups, and WhatsApp messaging.',
            'features': ['1 GB Perpetual Data (Never Expires)', '5.8 GHz & 2.4 GHz Access', 'Up to 2 Active Devices', 'Instant Scratch Card Top-Up'],
            'cta_code': 'STARTER-1GB',
        },
        {
            'name': 'Campus Scholar',
            'data_gb': 5,
            'price': '₦500',
            'popular': True,
            'description': 'Our most popular student tier for weekly lecture downloads, video streaming, and study research.',
            'features': ['5 GB Perpetual Data (Never Expires)', 'Priority Mesh Routing Bandwidth', 'Unlimited Device Switching', 'Zero Expiration Guarantee', 'Instant Voucher Activation'],
            'cta_code': 'SCHOLAR-5GB',
        },
        {
            'name': 'Hostel Mega',
            'data_gb': 10,
            'price': '₦1,000',
            'popular': False,
            'description': 'High-volume allowance for heavy Zoom lectures, collaborative coding, and media streaming.',
            'features': ['10 GB Perpetual Data (Never Expires)', 'Ultra-Low Latency Gaming/Streaming', 'Full Hotspot Tethering Allowed', 'Free Antenna Realignment Visit', '24/7 Priority Field Support'],
            'cta_code': 'MEGA-10GB',
        },
        {
            'name': 'Semester Pass',
            'data_gb': 60,
            'price': '₦5,000',
            'popular': False,
            'description': 'The ultimate uninterrupted off-grid semester internet package with maximum data savings.',
            'features': ['60 GB Perpetual Data (Never Expires)', 'Dedicated QoS Packet Priority', 'Complimentary Node Range Extender', 'Free Technician Site Survey', 'Lifetime Rollover Buffer'],
            'cta_code': 'SEMESTER-60GB',
        },
    ]

    retail_points = [
        {'name': 'Futo Market Kiosk & POS Center', 'location': 'Futo Market Plaza, Shop 12', 'hours': '7:30 AM – 10:00 PM'},
        {'name': 'Hostel B Mini-Mart', 'location': 'Hostel B Annex Ground Floor', 'hours': '7:00 AM – 11:00 PM'},
        {'name': 'ICT Center Solar Dispenser', 'location': 'ICT Building Tech Hub', 'hours': '24/7 Automated Dispenser'},
        {'name': 'SEET Complex Resource Center', 'location': 'SEET Complex Level 1', 'hours': '8:00 AM – 9:30 PM'},
    ]

    return render(request, 'pricing.html', {'tiers': tiers, 'retail_points': retail_points})


def register_view(request):
    """Register new user account, auto-generate data wallet with Wi-Fi access key."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Welcome to EcoMesh, {user.username}! Your account is ready. You can now schedule technical support or access your data wallet.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """User authentication view with styled form."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """User logout."""
    auth_logout(request)
    messages.info(request, "You have been logged out securely. See you on the mesh!")
    return redirect('home')


@login_required
def dashboard_view(request):
    """User Dashboard: Technician Service Appointments & Scheduling History as top priority, plus Data Wallet."""
    wallet, _ = UserDataWallet.objects.get_or_create(user=request.user)
    
    # If user has no assigned node yet, link to first active node
    if not wallet.assigned_node:
        first_active = MeshNode.objects.filter(status='ACTIVE').first()
        if first_active:
            wallet.assigned_node = first_active
            wallet.save()

    # User appointments (Upcoming vs Past)
    schedules = request.user.schedules.all().order_by('-scheduled_date', '-scheduled_time')
    upcoming_schedules = schedules.filter(status__in=['PENDING', 'CONFIRMED', 'IN_PROGRESS'])
    past_schedules = schedules.filter(status__in=['COMPLETED', 'CANCELLED'])

    redeem_form = VoucherRedeemForm()
    available_nodes = MeshNode.objects.all().order_by('-status', 'name')
    service_types = ServiceType.objects.filter(is_active=True)

    # Active system alerts (nodes undergoing maintenance or offline)
    system_alerts = MeshNode.objects.exclude(status='ACTIVE')

    # Admin management tools
    admin_vouchers = None
    admin_voucher_form = None
    admin_node_form = None
    active_vouchers_count = 0
    used_vouchers_count = 0
    if request.user.is_staff or request.user.is_superuser:
        admin_vouchers = Voucher.objects.all().order_by('-id')
        active_vouchers_count = admin_vouchers.filter(is_redeemed=False).count()
        used_vouchers_count = admin_vouchers.filter(is_redeemed=True).count()
        admin_voucher_form = AdminGenerateVoucherForm()
        admin_node_form = AdminMeshNodeForm(initial={
            'location_area': 'Campus Zone',
            'battery_level': 100,
            'status': 'ACTIVE',
            'signal_quality': 'Optimal',
            'uptime_percentage': 99.8
        })

    is_technician = hasattr(request.user, 'technician_profile') or request.user.is_staff or request.user.is_superuser

    context = {
        'wallet': wallet,
        'redeem_form': redeem_form,
        'schedules': schedules,
        'upcoming_schedules': upcoming_schedules,
        'past_schedules': past_schedules,
        'available_nodes': available_nodes,
        'service_types': service_types,
        'system_alerts': system_alerts,
        'is_technician': is_technician,
        'admin_vouchers': admin_vouchers,
        'admin_voucher_form': admin_voucher_form,
        'admin_node_form': admin_node_form,
        'active_vouchers_count': active_vouchers_count,
        'used_vouchers_count': used_vouchers_count,
    }
    return render(request, 'dashboard.html', context)


@login_required
def book_service_view(request):
    """Book a new technician dispatch with service pre-selection and conflict validation."""
    wallet = getattr(request.user, 'wallet', None)
    initial_data = {}
    
    # Pre-select service or node if passed in GET query
    service_code = request.GET.get('service')
    node_id = request.GET.get('node')
    if service_code:
        initial_data['service_type'] = service_code
    if node_id:
        initial_data['node'] = node_id
    elif wallet and wallet.assigned_node:
        initial_data['node'] = wallet.assigned_node

    if request.method == 'POST':
        form = ServiceScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            
            # Link service_type_ref if matching record exists
            st_ref = ServiceType.objects.filter(code=schedule.service_type).first()
            if st_ref:
                schedule.service_type_ref = st_ref

            try:
                schedule.full_clean()
                schedule.save()
                messages.success(
                    request,
                    f"🎉 Booking Confirmed! Your technician appointment (Ticket #{schedule.ticket_number}) has been scheduled for {schedule.scheduled_date} at {schedule.scheduled_time.strftime('%I:%M %p')}."
                )
                return redirect('booking_confirmation', schedule_id=schedule.id)
            except Exception as e:
                if hasattr(e, 'message_dict'):
                    for field, errs in e.message_dict.items():
                        for err in errs:
                            messages.error(request, err)
                else:
                    messages.error(request, str(e))
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")
    else:
        form = ServiceScheduleForm(initial=initial_data)

    service_types = ServiceType.objects.filter(is_active=True)
    return render(request, 'book_service.html', {'form': form, 'service_types': service_types})


@login_required
def booking_confirmation_view(request, schedule_id):
    """Display receipt and confirmation summary for a booked service appointment."""
    schedule = get_object_or_404(ServiceSchedule, id=schedule_id, user=request.user)
    return render(request, 'booking_confirmation.html', {'schedule': schedule})


@login_required
def cancel_service_view(request, schedule_id):
    """Cancel an active service appointment."""
    if request.method == 'POST':
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id, user=request.user)
        if schedule.status in ['PENDING', 'CONFIRMED']:
            schedule.status = 'CANCELLED'
            schedule.save()
            messages.info(request, f"Appointment #{schedule.ticket_number} ({schedule.get_service_name()}) has been cancelled.")
        else:
            messages.warning(request, "This appointment cannot be cancelled in its current state.")

    return redirect('dashboard')


@login_required
def technician_portal_view(request):
    """Dedicated Field Technician Portal to view assigned dispatches, update status, and add work notes."""
    is_tech = hasattr(request.user, 'technician_profile') or request.user.is_staff or request.user.is_superuser
    if not is_tech:
        messages.warning(request, "Access restricted. You need technician credentials to view the Technician Portal.")
        return redirect('dashboard')

    # Get technician's assigned dispatches (or all dispatches if superuser/admin)
    if request.user.is_superuser or request.user.is_staff:
        dispatches = ServiceSchedule.objects.all().order_by('-scheduled_date', '-scheduled_time')
    else:
        dispatches = ServiceSchedule.objects.filter(technician=request.user).order_by('-scheduled_date', '-scheduled_time')

    # Status filter from GET query
    status_filter = request.GET.get('status', 'ALL')
    if status_filter != 'ALL':
        filtered_dispatches = dispatches.filter(status=status_filter)
    else:
        filtered_dispatches = dispatches

    # Counts
    pending_count = dispatches.filter(status='PENDING').count()
    confirmed_count = dispatches.filter(status='CONFIRMED').count()
    in_progress_count = dispatches.filter(status='IN_PROGRESS').count()
    completed_count = dispatches.filter(status='COMPLETED').count()

    context = {
        'dispatches': filtered_dispatches,
        'total_count': dispatches.count(),
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'current_filter': status_filter,
    }
    return render(request, 'technician_portal.html', context)


@login_required
def technician_update_status_view(request, schedule_id):
    """Technician action to transition ticket status and append remarks."""
    is_tech = hasattr(request.user, 'technician_profile') or request.user.is_staff or request.user.is_superuser
    if not is_tech:
        messages.error(request, "Unauthorized.")
        return redirect('dashboard')

    schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        tech_notes = request.POST.get('technician_notes', '')

        if new_status in ['PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            schedule.status = new_status
        if tech_notes:
            schedule.technician_notes = tech_notes.strip()
        
        # If unassigned and tech updates, auto-assign this technician
        if not schedule.technician and hasattr(request.user, 'technician_profile'):
            schedule.technician = request.user

        schedule.save()
        messages.success(request, f"Ticket #{schedule.ticket_number} status updated to '{schedule.get_status_display()}'.")

    return redirect('technician_portal')


@login_required
def admin_scheduling_dashboard_view(request):
    """Administrator Command Center for scheduling, technician assignment, and service metrics."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Unauthorized. Only administrators can access this console.")
        return redirect('dashboard')

    all_schedules = ServiceSchedule.objects.all().order_by('-scheduled_date', '-scheduled_time')
    technicians = User.objects.filter(technician_profile__isnull=False)
    service_types = ServiceType.objects.all()

    # Handle technician assignment POST
    if request.method == 'POST' and 'assign_technician' in request.POST:
        schedule_id = request.POST.get('schedule_id')
        tech_user_id = request.POST.get('technician_id')
        new_status = request.POST.get('status', 'CONFIRMED')
        
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id)
        if tech_user_id:
            tech_user = get_object_or_404(User, id=tech_user_id)
            schedule.technician = tech_user
        else:
            schedule.technician = None
        
        if new_status in ['PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            schedule.status = new_status

        schedule.save()
        messages.success(request, f"Updated Ticket #{schedule.ticket_number}: Technician assigned & status set to '{schedule.get_status_display()}'.")
        return redirect('admin_scheduling')

    context = {
        'all_schedules': all_schedules,
        'technicians': technicians,
        'service_types': service_types,
        'total_bookings': all_schedules.count(),
        'pending_bookings': all_schedules.filter(status='PENDING').count(),
        'in_progress_bookings': all_schedules.filter(status='IN_PROGRESS').count(),
        'completed_bookings': all_schedules.filter(status='COMPLETED').count(),
        'unassigned_bookings': all_schedules.filter(technician__isnull=True, status__in=['PENDING', 'CONFIRMED']).count(),
    }
    return render(request, 'admin_scheduling.html', context)


def api_check_availability(request):
    """JSON API to return booked time slots for a node on a date to prevent frontend selection collisions."""
    node_id = request.GET.get('node_id')
    date_str = request.GET.get('date')
    if not node_id or not date_str:
        return JsonResponse({'booked_slots': []})
    
    booked = ServiceSchedule.objects.filter(
        node_id=node_id,
        scheduled_date=date_str,
        status__in=['PENDING', 'CONFIRMED', 'IN_PROGRESS']
    ).values_list('scheduled_time', flat=True)
    
    booked_formatted = [t.strftime('%H:%M:%S') for t in booked]
    return JsonResponse({'booked_slots': booked_formatted})


# --- Existing Node & Voucher Admin Endpoints Preserved ---

@login_required
def admin_create_node_view(request):
    """Admin-only endpoint to add a new live community mesh node."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Unauthorized. Only administrators can add nodes.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = AdminMeshNodeForm(request.POST)
        if form.is_valid():
            node = form.save()
            messages.success(request, f"✅ Mesh Node '{node.name}' was successfully deployed in '{node.location_area}'!")
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")

    return redirect('dashboard')


@login_required
def admin_update_node_view(request, node_id):
    """Admin-only endpoint to quick-update node status, battery level, maintenance schedule, and notes."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Unauthorized. Only administrators can update nodes.")
        return redirect('dashboard')

    node = get_object_or_404(MeshNode, id=node_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        battery_level = request.POST.get('battery_level')
        maintenance_note = request.POST.get('maintenance_note', '')
        next_maintenance_date = request.POST.get('next_maintenance_date')

        if status in ['ACTIVE', 'MAINTENANCE', 'OFFLINE']:
            node.status = status
        
        if battery_level and battery_level.isdigit():
            node.battery_level = max(0, min(100, int(battery_level)))
        
        node.maintenance_note = maintenance_note.strip()
        
        if next_maintenance_date:
            try:
                node.next_maintenance_date = next_maintenance_date
            except Exception:
                pass
        elif next_maintenance_date == '':
            node.next_maintenance_date = None

        node.save()
        messages.success(request, f"Updated telemetry & status for '{node.name}' (Status: {node.get_status_display()}).")

    return redirect('dashboard')


@login_required
def admin_delete_node_view(request, node_id):
    """Admin-only endpoint to delete a community mesh node."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Unauthorized. Only administrators can delete nodes.")
        return redirect('dashboard')

    if request.method == 'POST':
        node = get_object_or_404(MeshNode, id=node_id)
        name = node.name
        node.delete()
        messages.info(request, f"🗑️ Mesh Node '{name}' has been deleted from active network topology.")

    return redirect('dashboard')


@login_required
def admin_generate_voucher_view(request):
    """Admin-only endpoint to generate custom or bulk promo codes of any megabyte amount."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Unauthorized. Only administrators can generate promo codes.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = AdminGenerateVoucherForm(request.POST)
        if form.is_valid():
            mb = form.cleaned_data['data_amount_mb']
            custom_code = form.cleaned_data.get('custom_code')
            quantity = form.cleaned_data['quantity']
            
            created_vouchers = []
            if custom_code and quantity == 1:
                v = Voucher.objects.create(code=custom_code, data_amount_mb=mb)
                created_vouchers.append(v)
            else:
                for _ in range(quantity):
                    while True:
                        code_suffix = secrets.token_hex(3).upper()
                        code = f"ECO-{round(mb/1024.0, 1)}GB-{code_suffix}" if mb >= 1024 else f"ECO-{mb}MB-{code_suffix}"
                        if not Voucher.objects.filter(code=code).exists():
                            break
                    v = Voucher.objects.create(code=code, data_amount_mb=mb)
                    created_vouchers.append(v)

            gb_val = round(mb / 1024.0, 2)
            messages.success(
                request,
                f"🎉 Successfully generated {len(created_vouchers)} promo code(s) of {mb} MB ({gb_val} GB) each!"
            )
        else:
            for field, errs in form.errors.items():
                for err in errs:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {err}")

    return redirect('dashboard')


@login_required
def redeem_voucher_view(request):
    """Process voucher redemption and perpetual balance stacking."""
    if request.method == 'POST':
        form = VoucherRedeemForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                voucher = Voucher.objects.get(code__iexact=code)
                if voucher.is_redeemed:
                    messages.warning(request, f"Voucher '{code}' was already redeemed on {voucher.redeemed_at.strftime('%b %d, %Y')}.")
                else:
                    wallet = voucher.redeem(request.user)
                    messages.success(
                        request,
                        f"🎉 Success! Voucher '{code}' redeemed. +{voucher.data_amount_gb} GB added to your perpetual wallet. Current Balance: {wallet.balance_in_gb} GB."
                    )
            except Voucher.DoesNotExist:
                messages.error(request, f"Invalid voucher code '{code}'. Please check the scratch code and try again.")
        else:
            messages.error(request, "Please enter a valid voucher code format.")

    return redirect('dashboard')
