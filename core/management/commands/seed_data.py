import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import MeshNode, UserDataWallet, Voucher, ServiceSchedule, ServiceType, TechnicianProfile


class Command(BaseCommand):
    help = 'Seeds initial data for EcoMesh: service types, technicians, demo appointments, nodes, vouchers, and admin'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Seeding EcoMesh Technical Service & Scheduling database..."))

        # 1. Admin Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ecomesh.network',
                'first_name': 'Admin',
                'last_name': 'Operations',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("  [+] Superuser created: admin / admin123"))
        else:
            self.stdout.write("  [.] Superuser 'admin' already exists.")

        # 2. Service Types
        services_data = [
            {
                'name': 'New Node Setup & Antenna Mounting',
                'code': 'INSTALL',
                'description': 'Mount high-gain directional receiver antenna aligned to nearest solar mast with low-loss RF cabling.',
                'estimated_duration_minutes': 60,
                'price': 'Free for Active Students',
                'icon_name': 'radio',
                'badge_color': 'emerald',
            },
            {
                'name': 'Signal Alignment & Azimuth Range Boost',
                'code': 'REALIGN',
                'description': 'RF spectrum analysis, antenna azimuth optimization, and interference elimination for ultra-low latency.',
                'estimated_duration_minutes': 45,
                'price': 'Free for Active Students',
                'icon_name': 'activity',
                'badge_color': 'teal',
            },
            {
                'name': 'Solar Battery & Inverter Servicing',
                'code': 'SOLAR_REPAIR',
                'description': 'LiFePO4 battery cell balancing, MPPT solar controller check, and microgrid power health diagnostics.',
                'estimated_duration_minutes': 90,
                'price': 'Complimentary',
                'icon_name': 'sun',
                'badge_color': 'amber',
            },
            {
                'name': 'Emergency Offline Diagnostics & Repair',
                'code': 'EMERGENCY',
                'description': 'Rapid on-site emergency dispatch for sudden signal drops, router failures, or weather damage.',
                'estimated_duration_minutes': 30,
                'price': 'Priority Dispatch',
                'icon_name': 'zap',
                'badge_color': 'rose',
            },
            {
                'name': 'Captive Portal & Router Configuration',
                'code': 'ROUTER_CONFIG',
                'description': 'Custom SSID setup, WPA3 enterprise key configuration, and multi-device connection troubleshooting.',
                'estimated_duration_minutes': 30,
                'price': 'Free Support',
                'icon_name': 'wifi',
                'badge_color': 'cyan',
            },
            {
                'name': 'General Hardware Servicing & Cable Drop',
                'code': 'REPAIR',
                'description': 'RJ45 connector crimping, Cat6 cable drops to study desks, and hardware health auditing.',
                'estimated_duration_minutes': 60,
                'price': 'Hardware Included',
                'icon_name': 'cpu',
                'badge_color': 'purple',
            },
        ]
        for s in services_data:
            ServiceType.objects.update_or_create(code=s['code'], defaults=s)
        self.stdout.write(self.style.SUCCESS(f"  [+] Configured {len(services_data)} Service Types."))

        # 3. Sample Mesh Nodes
        nodes_data = [
            {
                'name': 'Hostel B',
                'location_area': 'Campus Zone',
                'battery_level': 98,
                'status': 'ACTIVE',
                'signal_quality': 'Optimal',
                'uptime_percentage': 99.9,
                'maintenance_note': 'Operating on primary 400W Monocrystalline array + 2.4kWh LiFePO4 battery bank.',
            },
            {
                'name': 'Futo market',
                'location_area': 'Campus Zone',
                'battery_level': 92,
                'status': 'ACTIVE',
                'signal_quality': 'Optimal',
                'uptime_percentage': 99.8,
                'maintenance_note': 'Connected to high-bandwidth backhaul relay.',
            },
            {
                'name': 'ICT',
                'location_area': 'Campus Zone',
                'battery_level': 64,
                'status': 'MAINTENANCE',
                'signal_quality': 'Good',
                'uptime_percentage': 98.4,
                'next_maintenance_date': timezone.now() + datetime.timedelta(days=1, hours=4),
                'maintenance_note': 'Scheduled MPPT firmware upgrade and directional antenna realigning.',
            },
            {
                'name': 'SEET Complex',
                'location_area': 'Campus Zone',
                'battery_level': 88,
                'status': 'ACTIVE',
                'signal_quality': 'Good',
                'uptime_percentage': 99.7,
                'maintenance_note': 'Triple-relay solar cluster operational with zero grid reliance.',
            },
            {
                'name': 'Tetfund Boys',
                'location_area': 'Campus Zone',
                'battery_level': 18,
                'status': 'OFFLINE',
                'signal_quality': 'Fair',
                'uptime_percentage': 94.2,
                'next_maintenance_date': timezone.now() + datetime.timedelta(hours=18),
                'maintenance_note': 'Battery reserve depleted due to tree shading; field dispatch scheduled.',
            },
        ]
        created_nodes = []
        for n in nodes_data:
            node, _ = MeshNode.objects.update_or_create(name=n['name'], defaults=n)
            created_nodes.append(node)
        self.stdout.write(self.style.SUCCESS(f"  [+] Configured {len(created_nodes)} Mesh Nodes."))

        # 4. Certified Field Technicians
        tech1_user, t1_created = User.objects.get_or_create(
            username='tech_emeka',
            defaults={
                'email': 'emeka.tech@ecomesh.network',
                'first_name': 'Emeka',
                'last_name': 'Okafor',
                'is_staff': True,
            }
        )
        if t1_created:
            tech1_user.set_password('password123')
            tech1_user.save()
        TechnicianProfile.objects.update_or_create(
            user=tech1_user,
            defaults={
                'full_name': 'Engr. Emeka Okafor',
                'phone_number': '+234 812 345 6789',
                'specialization': 'RF Azimuth Alignment & Solar Microgrids',
                'assigned_zone': 'Campus Hostels & North Zone',
                'is_available': True,
            }
        )

        tech2_user, t2_created = User.objects.get_or_create(
            username='tech_fatima',
            defaults={
                'email': 'fatima.tech@ecomesh.network',
                'first_name': 'Fatima',
                'last_name': 'Bello',
                'is_staff': True,
            }
        )
        if t2_created:
            tech2_user.set_password('password123')
            tech2_user.save()
        TechnicianProfile.objects.update_or_create(
            user=tech2_user,
            defaults={
                'full_name': 'Engr. Fatima Bello',
                'phone_number': '+234 803 987 6543',
                'specialization': 'Network Infrastructure & Router Diagnostics',
                'assigned_zone': 'ICT & South Campus Hostels',
                'is_available': True,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [+] Field Technicians initialized: tech_emeka, tech_fatima (pwd: password123)"))

        # 5. Demo Student User
        student_user, s_created = User.objects.get_or_create(
            username='student1',
            defaults={
                'email': 'student@university.edu',
                'first_name': 'Alex',
                'last_name': 'Rivera',
            }
        )
        if s_created:
            student_user.set_password('password123')
            student_user.save()

        # Seed Student Wallet with 12.5 GB
        wallet, _ = UserDataWallet.objects.get_or_create(
            user=student_user,
            defaults={
                'balance_mb': 12800,
                'assigned_node': created_nodes[0],
            }
        )

        # 6. Sample Scheduled Appointments for student1
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        next_week = timezone.localdate() + datetime.timedelta(days=4)
        last_week = timezone.localdate() - datetime.timedelta(days=7)

        # Clear existing sample schedules for student1 to avoid conflicts
        ServiceSchedule.objects.filter(user=student_user).delete()

        # Upcoming appointment 1 (Confirmed)
        ServiceSchedule.objects.create(
            user=student_user,
            node=created_nodes[0],
            service_type='REALIGN',
            service_type_ref=ServiceType.objects.filter(code='REALIGN').first(),
            technician=tech1_user,
            address='Room 304, Hostel B Annex, South Campus',
            scheduled_date=tomorrow,
            scheduled_time=datetime.time(10, 30),
            status='CONFIRMED',
            notes='Signal strength dropped to 2 bars during heavy rain.',
            technician_notes='Dispatch confirmed. Engineer will carry spectrum analyzer and 5GHz replacement feedhorn.'
        )

        # Upcoming appointment 2 (Pending Review)
        ServiceSchedule.objects.create(
            user=student_user,
            node=created_nodes[1],
            service_type='INSTALL',
            service_type_ref=ServiceType.objects.filter(code='INSTALL').first(),
            address='Futo Market Shop 14 Plaza',
            scheduled_date=next_week,
            scheduled_time=datetime.time(14, 0),
            status='PENDING',
            notes='Requesting high-gain directional receiver antenna mounted on shop roof.',
        )

        # Past appointment 3 (Completed)
        ServiceSchedule.objects.create(
            user=student_user,
            node=created_nodes[0],
            service_type='ROUTER_CONFIG',
            service_type_ref=ServiceType.objects.filter(code='ROUTER_CONFIG').first(),
            technician=tech2_user,
            address='Room 304, Hostel B Annex',
            scheduled_date=last_week,
            scheduled_time=datetime.time(12, 0),
            status='COMPLETED',
            notes='Need captive portal assistance for laptop and iPad.',
            technician_notes='Successfully provisioned WPA3 enterprise credentials and verified 45Mbps throughput.'
        )

        self.stdout.write(self.style.SUCCESS("  [+] Sample appointments created for demo student."))

        # 7. Promo Vouchers
        vouchers_data = [
            {'code': 'ECO-10GB-SUN', 'data_amount_mb': 10240},
            {'code': 'ECO-25GB-PWR', 'data_amount_mb': 25600},
            {'code': 'ECO-05GB-MESH', 'data_amount_mb': 5120},
            {'code': 'ECO-50GB-MEGA', 'data_amount_mb': 51200},
            {'code': 'ECO-15GB-SCHOLAR', 'data_amount_mb': 15360},
        ]
        for v in vouchers_data:
            Voucher.objects.get_or_create(code=v['code'], defaults=v)
        self.stdout.write(self.style.SUCCESS("  [+] Promotional Vouchers initialized."))

        self.stdout.write(self.style.SUCCESS("\n[OK] EcoMesh database seeded successfully! Ready for SEN 310 assignment demonstration."))
