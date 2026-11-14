from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, FarmerProfile, BuyerProfile


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_farmer_registration(self):
        url = reverse('auth-register')
        data = {
            'email': 'newfarmer@test.com',
            'password': 'password123',
            'full_name': 'Test Farmer',
            'role': 'farmer',
            'phone': '9876543210',
            'farm_name': 'Green Acres',
            'village': 'Hoskote',
            'district': 'Bengaluru Rural',
            'state': 'Karnataka',
            'farm_size': 5.5,
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertEqual(res.data['user']['email'], 'newfarmer@test.com')
        self.assertEqual(res.data['user']['role'], 'farmer')
        self.assertTrue(User.objects.filter(email='newfarmer@test.com').exists())
        self.assertTrue(FarmerProfile.objects.filter(farm_name='Green Acres').exists())

    def test_buyer_registration(self):
        url = reverse('auth-register')
        data = {
            'email': 'newbuyer@test.com',
            'password': 'password123',
            'full_name': 'Agro Retailers',
            'role': 'buyer',
            'phone': '9876543211',
            'company_name': 'Agro Retailers Ltd',
            'contact_person': 'Jane Doe',
            'business_type': 'Retailer',
            'city': 'Mysuru',
            'district': 'Mysuru',
            'state': 'Karnataka',
            'interested_crops': ['Tomato', 'Potato'],
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertEqual(res.data['user']['role'], 'buyer')
        self.assertTrue(BuyerProfile.objects.filter(company_name='Agro Retailers Ltd').exists())

    def test_login_success(self):
        user = User.objects.create_user(
            email='loginuser@test.com',
            password='testpassword',
            full_name='Login User',
            role='farmer'
        )
        url = reverse('auth-login')
        res = self.client.post(url, {'email': 'loginuser@test.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])

    def test_suspended_user_cannot_login(self):
        user = User.objects.create_user(
            email='suspended@test.com',
            password='testpassword',
            full_name='Suspended User',
            role='farmer',
            account_status='suspended'
        )
        url = reverse('auth-login')
        res = self.client.post(url, {'email': 'suspended@test.com', 'password': 'testpassword'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
