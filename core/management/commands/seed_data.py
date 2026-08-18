import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import MeshNode, UserDataWallet, Voucher, ServiceSchedule


class Command(BaseCommand):
    help = 'Seeds initial data for EcoMesh: demo nodes, vouchers, demo student, and admin user'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Seeding EcoMesh database..."))

        # 1. Admin Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ecomesh.network',
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

        # 2. Sample Mesh Nodes with updated names & locations
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

        # Clear legacy node names if needed and recreate
        created_nodes = []
        for n in nodes_data:
            node, _ = MeshNode.objects.update_or_create(
                name=n['name'],
                defaults=n
            )
            created_nodes.append(node)
        self.stdout.write(self.style.SUCCESS(f"  [+] Configured {len(created_nodes)} Mesh Nodes."))

        # 3. Demo Student User
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
            self.stdout.write(self.style.SUCCESS("  [+] Demo Student created: student1 / password123"))

        # Initialize student data wallet with 12.5 GB (12800 MB)
        wallet, w_created = UserDataWallet.objects.get_or_create(
            user=student_user,
            defaults={
                'balance_mb': 12800,
                'assigned_node': created_nodes[0],
            }
        )
        if not w_created and wallet.balance_mb == 0:
            wallet.balance_mb = 12800
            wallet.assigned_node = created_nodes[0]
            wallet.save()
        self.stdout.write(self.style.SUCCESS(f"  [+] Initialized Data Wallet for {student_user.username} (Key: {wallet.wifi_access_key})"))

        # 4. Ready-to-Redeem Vouchers
        vouchers_data = [
            ('ECO-10GB-SUN', 10240),
            ('ECO-25GB-PWR', 25600),
            ('ECO-05GB-MESH', 5120),
            ('ECO-50GB-MEGA', 51200),
            ('ECO-15GB-SCHOLAR', 15360),
            ('ECO-05GB-TEST1', 5120),
            ('ECO-10GB-TEST2', 10240),
            ('ECO-20GB-SOLAR', 20480),
        ]

        v_count = 0
        for code, mb in vouchers_data:
            _, created_v = Voucher.objects.get_or_create(
                code=code,
                defaults={'data_amount_mb': mb, 'is_redeemed': False}
            )
            if created_v:
                v_count += 1
        self.stdout.write(self.style.SUCCESS(f"  [+] Created {v_count} fresh unredeemed vouchers."))

        # 5. Sample Service Schedules for Demo
        ServiceSchedule.objects.get_or_create(
            user=student_user,
            node=created_nodes[0],
            service_type='INSTALL',
            scheduled_date=timezone.localdate() + datetime.timedelta(days=2),
            scheduled_time=datetime.time(14, 30),
            defaults={
                'address': 'Room 312, Hostel B',
                'status': 'CONFIRMED',
                'notes': 'Need high-gain directional antenna installed facing Hostel B Hub for lowest gaming latency.',
            }
        )

        ServiceSchedule.objects.get_or_create(
            user=student_user,
            node=created_nodes[3],
            service_type='REALIGN',
            scheduled_date=timezone.localdate() + datetime.timedelta(days=5),
            scheduled_time=datetime.time(10, 0),
            defaults={
                'address': 'SEET Complex Room 14',
                'status': 'PENDING',
                'notes': 'Checking signal strength after renovation.',
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] EcoMesh database seeding completed successfully!"))
