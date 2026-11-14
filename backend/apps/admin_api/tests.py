from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, FarmerProfile


class AdminAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='password123',
            full_name='Admin User',
            role='admin',
            is_staff=True
        )

        self.farmer = User.objects.create_user(
            email='farmer@test.com',
            password='password123',
            full_name='Farmer One',
            role='farmer',
            is_verified=False
        )

    def test_admin_analytics_requires_admin_role(self):
        self.client.force_authenticate(user=self.farmer)
        url = reverse('admin-analytics')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_analytics(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('admin-analytics')
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('users', res.data)
        self.assertIn('listings', res.data)
        self.assertIn('orders', res.data)

    def test_admin_can_verify_and_suspend_user(self):
        self.client.force_authenticate(user=self.admin)

        # 1. Verify user
        verify_url = reverse('admin-user-verify', kwargs={'pk': str(self.farmer.id)})
        res = self.client.patch(verify_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.farmer.refresh_from_db()
        self.assertTrue(self.farmer.is_verified)

        # 2. Suspend user
        suspend_url = reverse('admin-user-suspend', kwargs={'pk': str(self.farmer.id)})
        res = self.client.patch(suspend_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.account_status, 'suspended')

        # 3. Reactivate user
        reactivate_url = reverse('admin-user-reactivate', kwargs={'pk': str(self.farmer.id)})
        res = self.client.patch(reactivate_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.farmer.refresh_from_db()
        self.assertEqual(self.farmer.account_status, 'active')
