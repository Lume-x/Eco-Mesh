import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from .models import MeshNode, UserDataWallet, Voucher, ServiceSchedule


class EcoMeshModelTests(TestCase):
    def setUp(self):
        self.node1 = MeshNode.objects.create(
            name="Hostel Block A - Primary",
            location_area="Hostel Block A",
            battery_level=95,
            status="ACTIVE",
            signal_quality="Optimal",
            uptime_percentage=99.9,
            maintenance_note="Fully operational"
        )
        self.user = User.objects.create_user(
            username="teststudent",
            email="teststudent@university.edu",
            password="testpassword123"
        )

    def test_user_data_wallet_auto_wifi_key_and_gb_conversion(self):
        wallet = UserDataWallet.objects.create(
            user=self.user,
            balance_mb=10240, # 10 GB
            assigned_node=self.node1
        )
        self.assertIsNotNone(wallet.wifi_access_key)
        self.assertEqual(len(wallet.wifi_access_key), 8)
        self.assertTrue(wallet.wifi_access_key.isupper())
        self.assertEqual(wallet.balance_in_gb, 10.0)

    def test_voucher_redemption_and_balance_stacking(self):
        wallet = UserDataWallet.objects.create(
            user=self.user,
            balance_mb=2048, # 2 GB initial
            assigned_node=self.node1
        )
        voucher = Voucher.objects.create(
            code="ECO-15GB-TEST",
            data_amount_mb=15360 # 15 GB
        )
        self.assertFalse(voucher.is_redeemed)

        # Redeem voucher
        updated_wallet = voucher.redeem(self.user)
        voucher.refresh_from_db()

        self.assertTrue(voucher.is_redeemed)
        self.assertEqual(voucher.redeemed_by, self.user)
        self.assertIsNotNone(voucher.redeemed_at)
        self.assertEqual(updated_wallet.balance_mb, 2048 + 15360)
        self.assertEqual(updated_wallet.balance_in_gb, 17.0)

        # Re-redemption must raise ValidationError
        with self.assertRaises(ValidationError):
            voucher.redeem(self.user)

    def test_service_schedule_clean_conflict_validation(self):
        booking_date = timezone.localdate() + datetime.timedelta(days=3)
        booking_time = datetime.time(14, 0)

        # First booking succeeds
        schedule1 = ServiceSchedule(
            user=self.user,
            node=self.node1,
            service_type="INSTALL",
            address="Room 101",
            scheduled_date=booking_date,
            scheduled_time=booking_time,
            status="PENDING"
        )
        schedule1.full_clean()
        schedule1.save()

        # Second user attempts to book same node and same slot
        user2 = User.objects.create_user(username="student2", password="password123")
        schedule2 = ServiceSchedule(
            user=user2,
            node=self.node1,
            service_type="REALIGN",
            address="Room 102",
            scheduled_date=booking_date,
            scheduled_time=booking_time,
            status="PENDING"
        )

        with self.assertRaises(ValidationError):
            schedule2.full_clean()


class EcoMeshViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.node = MeshNode.objects.create(
            name="Hostel Block B - Hub",
            location_area="Hostel Block B",
            battery_level=89,
            status="ACTIVE"
        )
        self.user = User.objects.create_user(
            username="demouser",
            email="demo@ecomesh.network",
            password="demopassword123"
        )
        self.wallet = UserDataWallet.objects.create(
            user=self.user,
            balance_mb=5120,
            assigned_node=self.node
        )
        self.voucher = Voucher.objects.create(
            code="ECO-10GB-UNITTEST",
            data_amount_mb=10240
        )

    def test_public_pages_render_successfully(self):
        routes = [
            reverse('home'),
            reverse('about'),
            reverse('team'),
            reverse('pricing'),
            reverse('login'),
            reverse('register'),
        ]
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed on URL: {url}")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_dashboard_renders_for_logged_in_user(self):
        self.client.login(username="demouser", password="demopassword123")
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Perpetual Data Wallet")
        self.assertContains(response, "5.0") # 5.0 GB
        self.assertContains(response, self.wallet.wifi_access_key)

    def test_redeem_voucher_view(self):
        self.client.login(username="demouser", password="demopassword123")
        response = self.client.post(reverse('redeem_voucher'), {'code': 'ECO-10GB-UNITTEST'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance_mb, 5120 + 10240)
        self.assertEqual(self.wallet.balance_in_gb, 15.0)

    def test_book_service_and_cancel_view(self):
        self.client.login(username="demouser", password="demopassword123")
        booking_date = (timezone.localdate() + datetime.timedelta(days=4)).isoformat()
        
        # Book service
        response = self.client.post(reverse('book_service'), {
            'service_type': 'INSTALL',
            'node': self.node.id,
            'address': 'Room 505',
            'scheduled_date': booking_date,
            'scheduled_time': '11:00',
            'notes': 'Please check signal strength.'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        schedule = ServiceSchedule.objects.filter(user=self.user, address='Room 505').first()
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.status, 'PENDING')

        # Cancel service
        cancel_response = self.client.post(reverse('cancel_service', args=[schedule.id]), follow=True)
        self.assertEqual(cancel_response.status_code, 200)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, 'CANCELLED')

    def test_admin_generate_voucher_view(self):
        # Regular student cannot generate vouchers
        self.client.login(username="demouser", password="demopassword123")
        res = self.client.post(reverse('admin_generate_voucher'), {
            'data_amount_mb': 10240,
            'quantity': 1
        }, follow=True)
        self.assertContains(res, "Unauthorized")

        # Admin / Staff user can generate custom promo codes
        admin_user = User.objects.create_superuser(
            username="testadmin",
            password="adminpassword123",
            email="admin@test.com"
        )
        self.client.login(username="testadmin", password="adminpassword123")
        admin_res = self.client.post(reverse('admin_generate_voucher'), {
            'data_amount_mb': 20480, # 20 GB
            'custom_code': 'SPECIAL-20GB-PROMO',
            'quantity': 1
        }, follow=True)
        self.assertEqual(admin_res.status_code, 200)
        self.assertTrue(Voucher.objects.filter(code='SPECIAL-20GB-PROMO', data_amount_mb=20480).exists())
        self.assertContains(admin_res, "SPECIAL-20GB-PROMO")

    def test_admin_node_management_operations(self):
        admin_user = User.objects.create_superuser(
            username="nodeadmin",
            password="adminpassword123",
            email="nodeadmin@test.com"
        )
        self.client.login(username="nodeadmin", password="adminpassword123")

        # 1. Create Node
        create_res = self.client.post(reverse('admin_create_node'), {
            'name': 'Tetfund Annex Node',
            'location_area': 'Campus Zone',
            'battery_level': 95,
            'status': 'ACTIVE',
            'signal_quality': 'Optimal',
            'uptime_percentage': 99.9,
            'maintenance_note': 'Brand new solar array'
        }, follow=True)
        self.assertEqual(create_res.status_code, 200)
        node = MeshNode.objects.filter(name='Tetfund Annex Node').first()
        self.assertIsNotNone(node)

        # 2. Update Node (toggle to MAINTENANCE, update battery & note)
        update_res = self.client.post(reverse('admin_update_node', args=[node.id]), {
            'status': 'MAINTENANCE',
            'battery_level': 75,
            'maintenance_note': 'Scheduled MPPT inspection'
        }, follow=True)
        self.assertEqual(update_res.status_code, 200)
        node.refresh_from_db()
        self.assertEqual(node.status, 'MAINTENANCE')
        self.assertEqual(node.battery_level, 75)

        # 3. Delete Node
        delete_res = self.client.post(reverse('admin_delete_node', args=[node.id]), follow=True)
        self.assertEqual(delete_res.status_code, 200)
        self.assertFalse(MeshNode.objects.filter(name='Tetfund Annex Node').exists())
