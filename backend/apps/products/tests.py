import io
from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, FarmerProfile, BuyerProfile
from apps.products.models import ProductListing, QualityAssessment


class ProductAndAITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.farmer = User.objects.create_user(
            email='farmer1@test.com',
            password='password123',
            full_name='Farmer One',
            role='farmer'
        )
        FarmerProfile.objects.create(
            user=self.farmer,
            farm_name='Test Farm',
            district='Kolar',
            state='Karnataka'
        )

        self.buyer = User.objects.create_user(
            email='buyer1@test.com',
            password='password123',
            full_name='Buyer One',
            role='buyer'
        )
        BuyerProfile.objects.create(
            user=self.buyer,
            company_name='Buyer Co',
            district='Bengaluru Urban'
        )

    def _create_sample_image(self):
        img = Image.new('RGB', (100, 100), color=(180, 50, 40))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return SimpleUploadedFile('test_tomato.jpg', buf.read(), content_type='image/jpeg')

    def test_quality_assessment_api(self):
        self.client.force_authenticate(user=self.farmer)
        url = reverse('ai-quality-assessment')
        img_file = self._create_sample_image()
        res = self.client.post(url, {'image': img_file, 'crop': 'Tomato'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('predicted_grade', res.data)
        self.assertIn('confidence', res.data)
        self.assertEqual(res.data['assessment_method'], 'pixel_heuristic_demo')
        self.assertTrue(QualityAssessment.objects.filter(farmer=self.farmer).exists())

    def test_farmer_can_create_product(self):
        self.client.force_authenticate(user=self.farmer)
        url = reverse('product-list-create')
        data = {
            'product_name': 'Fresh Red Tomato',
            'crop': 'Tomato',
            'quantity': 500,
            'unit': 'kg',
            'asking_price': 25.0,
            'quality_grade': 'A',
            'quality_confidence': 90,
            'harvest_date': '2026-11-12',
            'district': 'Kolar',
            'status': 'active',
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['product_name'], 'Fresh Red Tomato')
        self.assertEqual(ProductListing.objects.filter(farmer=self.farmer).count(), 1)

    def test_buyer_cannot_create_product(self):
        self.client.force_authenticate(user=self.buyer)
        url = reverse('product-list-create')
        data = {
            'product_name': 'Buyer Listing',
            'crop': 'Tomato',
            'quantity': 100,
            'asking_price': 20.0,
            'quality_grade': 'B',
            'harvest_date': '2026-11-12',
            'district': 'Bengaluru Urban',
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
