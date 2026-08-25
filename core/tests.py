import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from .models import MeshNode, UserDataWallet, Voucher, ServiceSchedule, ServiceType, TechnicianProfile


class EcoMeshModelTests(TestCase):
    def setUp(self):
        self.node1 = MeshNode.objects.create(
            name="Hostel Block A - Primary",
            location_area="Campus Zone",
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
        self.service_type = ServiceType.objects.create(
            name="Signal Alignment & Azimuth Boost",
            code="REALIGN",
            description="RF spectrum analyzer optimization",
            estimated_duration_minutes=45
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

    def test_service_schedule_conflict_validation(self):
        booking_date = timezone.localdate() + datetime.timedelta(days=3)
        booking_time = datetime.time(10, 30)

        # First booking succeeds
        schedule1 = ServiceSchedule(
            user=self.user,
            node=self.node1,
            service_type="REALIGN",
            service_type_ref=self.service_type,
            address="Room 101",
            scheduled_date=booking_date,
            scheduled_time=booking_time,
            status="PENDING"
        )
        schedule1.full_clean()
        schedule1.save()
        self.assertEqual(schedule1.ticket_number, f"ECO-{schedule1.id:04d}")

        # Second user attempts to book same node and same slot -> Conflict error
        user2 = User.objects.create_user(username="student2", password="password123")
        schedule2 = ServiceSchedule(
            user=user2,
            node=self.node1,
            service_type="INSTALL",
            address="Room 102",
            scheduled_date=booking_date,
            scheduled_time=booking_time,
            status="PENDING"
        )

        with self.assertRaises(ValidationError):
            schedule2.full_clean()

    def test_past_date_booking_rejected(self):
        past_date = timezone.localdate() - datetime.timedelta(days=1)
        schedule = ServiceSchedule(
            user=self.user,
            node=self.node1,
            service_type="INSTALL",
            address="Room 101",
            scheduled_date=past_date,
            scheduled_time=datetime.time(14, 0)
        )
        with self.assertRaises(ValidationError):
            schedule.full_clean()


class EcoMeshSchedulingWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.node = MeshNode.objects.create(
            name="Hostel B",
            location_area="Campus Zone",
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
        self.service_type = ServiceType.objects.create(
            name="New Node Setup & Antenna Mounting",
            code="INSTALL",
            description="Mount antenna",
            estimated_duration_minutes=60
        )
        
        # Technician user
        self.tech_user = User.objects.create_user(
            username="tech_john",
            email="john@tech.network",
            password="password123",
            first_name="John",
            last_name="Doe",
            is_staff=True
        )
        self.tech_profile = TechnicianProfile.objects.create(
            user=self.tech_user,
            full_name="John Doe",
            phone_number="+234 811 111 2222",
            specialization="RF & Solar"
        )

        # Admin user
        self.admin_user = User.objects.create_superuser(
            username="superadmin",
            email="superadmin@ecomesh.network",
            password="adminpassword123"
        )

    def test_public_pages_render_with_saas_scheduling_focus(self):
        routes = [
            reverse('home'),
            reverse('services'),
            reverse('about'),
            reverse('team'),
            reverse('pricing'),
            reverse('login'),
            reverse('register'),
        ]
        for url in routes:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed on URL: {url}")
        
        # Home must prominently feature headline and CTA
        home_res = self.client.get(reverse('home'))
        self.assertContains(home_res, "Stay Connected. Get Technical Support When You Need It.")
        self.assertContains(home_res, "Book a Technician")
        self.assertContains(home_res, "Technical Services")

    def test_complete_booking_workflow(self):
        self.client.login(username="demouser", password="demopassword123")
        booking_date = (timezone.localdate() + datetime.timedelta(days=2)).isoformat()

        response = self.client.post(reverse('book_service'), {
            'service_type': 'INSTALL',
            'node': self.node.id,
            'address': 'Room 408, Hostel B',
            'scheduled_date': booking_date,
            'scheduled_time': '09:00:00',
            'notes': 'Antenna bracket required.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        schedule = ServiceSchedule.objects.filter(user=self.user, address='Room 408, Hostel B').first()
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.status, 'PENDING')
        self.assertContains(response, "Booking Confirmed")
        self.assertContains(response, schedule.ticket_number)

    def test_dashboard_displays_upcoming_and_kpis(self):
        self.client.login(username="demouser", password="demopassword123")
        
        future_date = timezone.localdate() + datetime.timedelta(days=3)
        appt = ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 101",
            scheduled_date=future_date,
            scheduled_time=datetime.time(10, 30),
            status="CONFIRMED",
            technician=self.tech_user
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back,")
        self.assertContains(response, "UPCOMING APPOINTMENT")
        self.assertContains(response, appt.ticket_number)
        self.assertContains(response, "Total Appointments")

    def test_my_appointments_page_and_tabs(self):
        self.client.login(username="demouser", password="demopassword123")
        future_date = timezone.localdate() + datetime.timedelta(days=3)
        appt = ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 101",
            scheduled_date=future_date,
            scheduled_time=datetime.time(10, 30),
            status="PENDING"
        )

        res_all = self.client.get(reverse('my_appointments'))
        self.assertEqual(res_all.status_code, 200)
        self.assertContains(res_all, "My Appointments")
        self.assertContains(res_all, appt.ticket_number)

        res_pending = self.client.get(reverse('my_appointments') + "?status=PENDING")
        self.assertEqual(res_pending.status_code, 200)
        self.assertContains(res_pending, appt.ticket_number)

    def test_cancel_appointment_action(self):
        self.client.login(username="demouser", password="demopassword123")
        future_date = timezone.localdate() + datetime.timedelta(days=3)
        appt = ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 101",
            scheduled_date=future_date,
            scheduled_time=datetime.time(10, 30),
            status="PENDING"
        )
        
        cancel_res = self.client.post(reverse('cancel_service', args=[appt.id]), follow=True)
        self.assertEqual(cancel_res.status_code, 200)
        appt.refresh_from_db()
        self.assertEqual(appt.status, 'CANCELLED')

    def test_technician_portal_and_status_transitions(self):
        # Regular student cannot access tech portal
        self.client.login(username="demouser", password="demopassword123")
        res = self.client.get(reverse('technician_portal'), follow=True)
        self.assertContains(res, "Access restricted")

        # Technician logs in
        self.client.login(username="tech_john", password="password123")
        appt = ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 202",
            scheduled_date=timezone.localdate() + datetime.timedelta(days=1),
            scheduled_time=datetime.time(12, 0),
            status="CONFIRMED",
            technician=self.tech_user
        )

        portal_res = self.client.get(reverse('technician_portal'))
        self.assertEqual(portal_res.status_code, 200)
        self.assertContains(portal_res, appt.ticket_number)

        update_res = self.client.post(reverse('technician_update_status', args=[appt.id]), {
            'status': 'COMPLETED',
            'technician_notes': 'Antenna aligned perfectly. Signal -58dBm.'
        }, follow=True)
        self.assertEqual(update_res.status_code, 200)
        appt.refresh_from_db()
        self.assertEqual(appt.status, 'COMPLETED')
        self.assertEqual(appt.technician_notes, 'Antenna aligned perfectly. Signal -58dBm.')

    def test_admin_scheduling_dashboard_and_technician_assignment(self):
        self.client.login(username="superadmin", password="adminpassword123")
        
        unassigned_appt = ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 303",
            scheduled_date=timezone.localdate() + datetime.timedelta(days=2),
            scheduled_time=datetime.time(14, 0),
            status="PENDING"
        )

        admin_page = self.client.get(reverse('admin_scheduling'))
        self.assertEqual(admin_page.status_code, 200)
        self.assertContains(admin_page, "Admin Operations")
        self.assertContains(admin_page, unassigned_appt.ticket_number)

        assign_res = self.client.post(reverse('admin_scheduling'), {
            'assign_technician': '1',
            'schedule_id': unassigned_appt.id,
            'technician_id': self.tech_user.id,
            'status': 'CONFIRMED'
        }, follow=True)

        self.assertEqual(assign_res.status_code, 200)
        unassigned_appt.refresh_from_db()
        self.assertEqual(unassigned_appt.technician, self.tech_user)
        self.assertEqual(unassigned_appt.status, 'CONFIRMED')

    def test_api_check_availability_endpoint(self):
        booking_date = (timezone.localdate() + datetime.timedelta(days=2)).isoformat()
        ServiceSchedule.objects.create(
            user=self.user,
            node=self.node,
            service_type="INSTALL",
            address="Room 500",
            scheduled_date=booking_date,
            scheduled_time=datetime.time(9, 0),
            status="CONFIRMED"
        )

        api_res = self.client.get(f"/api/check-availability/?node_id={self.node.id}&date={booking_date}")
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertIn("09:00:00", data['booked_slots'])
