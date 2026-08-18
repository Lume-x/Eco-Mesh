from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from django.utils import timezone
from .models import MeshNode, UserDataWallet, Voucher, ServiceSchedule
from .forms import UserRegistrationForm, UserLoginForm, VoucherRedeemForm, ServiceScheduleForm


def home_view(request):
    """Public landing page featuring live node coverage grid, solar metrics, and tech overview."""
    nodes = MeshNode.objects.all()
    active_nodes = nodes.filter(status='ACTIVE')
    maintenance_nodes = nodes.filter(status='MAINTENANCE')
    offline_nodes = nodes.filter(status='OFFLINE')

    total_nodes_count = nodes.count()
    active_nodes_count = active_nodes.count()
    
    # Calculate live system metrics
    avg_uptime = nodes.aggregate(Avg('uptime_percentage'))['uptime_percentage__avg'] or 99.8
    total_wallets = UserDataWallet.objects.count()
    connected_peers = max(184, total_wallets * 12 + 42) # Realistic dynamic community multiplier
    solar_co2_offset = round((active_nodes_count or 4) * 148.6, 1)

    context = {
        'nodes': nodes,
        'active_nodes_count': active_nodes_count,
        'maintenance_nodes_count': maintenance_nodes.count(),
        'offline_nodes_count': offline_nodes.count(),
        'total_nodes_count': total_nodes_count,
        'avg_uptime': round(avg_uptime, 1),
        'connected_peers': connected_peers,
        'solar_co2_offset': solar_co2_offset,
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
            messages.success(request, f"Welcome to EcoMesh, {user.username}! Your perpetual data wallet and 500 MB welcome grant are ready.")
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


import secrets
from .forms import UserRegistrationForm, UserLoginForm, VoucherRedeemForm, ServiceScheduleForm, AdminGenerateVoucherForm, AdminMeshNodeForm


@login_required
def dashboard_view(request):
    """Client Portal: Perpetual Data Wallet, Wi-Fi Access Key, Connected Node Status, and Bookings."""
    wallet, _ = UserDataWallet.objects.get_or_create(user=request.user)
    
    # If user has no assigned node yet, link to first active node
    if not wallet.assigned_node:
        first_active = MeshNode.objects.filter(status='ACTIVE').first()
        if first_active:
            wallet.assigned_node = first_active
            wallet.save()

    redeem_form = VoucherRedeemForm()
    schedules = request.user.schedules.all()
    available_nodes = MeshNode.objects.all().order_by('-status', 'name')

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

    context = {
        'wallet': wallet,
        'redeem_form': redeem_form,
        'schedules': schedules,
        'available_nodes': available_nodes,
        'system_alerts': system_alerts,
        'admin_vouchers': admin_vouchers,
        'admin_voucher_form': admin_voucher_form,
        'admin_node_form': admin_node_form,
        'active_vouchers_count': active_vouchers_count,
        'used_vouchers_count': used_vouchers_count,
    }
    return render(request, 'dashboard.html', context)


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


@login_required
def book_service_view(request):
    """Book a new technician dispatch or node alignment service."""
    wallet = getattr(request.user, 'wallet', None)
    initial_data = {}
    if wallet and wallet.assigned_node:
        initial_data['node'] = wallet.assigned_node

    if request.method == 'POST':
        form = ServiceScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            try:
                schedule.full_clean()
                schedule.save()
                messages.success(
                    request,
                    f"✅ Service request booked for {schedule.scheduled_date} at {schedule.scheduled_time.strftime('%H:%M')}! A field engineer will confirm your slot shortly."
                )
                return redirect('dashboard')
            except Exception as e:
                # Catch clean() validation errors
                if hasattr(e, 'message_dict'):
                    for field, errs in e.message_dict.items():
                        for err in errs:
                            messages.error(request, err)
                else:
                    messages.error(request, str(e))
        else:
            messages.error(request, "Please fix the errors indicated in the booking form.")
    else:
        form = ServiceScheduleForm(initial=initial_data)

    return render(request, 'book_service.html', {'form': form})


@login_required
def cancel_service_view(request, schedule_id):
    """Cancel an active service appointment."""
    if request.method == 'POST':
        schedule = get_object_or_404(ServiceSchedule, id=schedule_id, user=request.user)
        if schedule.status in ['PENDING', 'CONFIRMED']:
            schedule.status = 'CANCELLED'
            schedule.save()
            messages.info(request, f"Appointment #{schedule.id} ({schedule.get_service_type_display()}) has been cancelled.")
        else:
            messages.warning(request, "This appointment cannot be cancelled in its current state.")

    return redirect('dashboard')
