from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import User, FarmerProfile, BuyerProfile
from apps.products.models import ProductListing
from apps.bids.models import Bid
from apps.orders.models import Order


class BiddingAndOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Farmer
        self.farmer = User.objects.create_user(
            email='farmer@test.com',
            password='password123',
            full_name='Ramesh K',
            role='farmer',
            is_verified=True
        )
        FarmerProfile.objects.create(
            user=self.farmer,
            farm_name='Ramesh Farm',
            district='Kolar',
            state='Karnataka'
        )

        # Verified Buyer
        self.buyer_verified = User.objects.create_user(
            email='verified_buyer@test.com',
            password='password123',
            full_name='Wholesale Ltd',
            role='buyer',
            is_verified=True
        )
        BuyerProfile.objects.create(
            user=self.buyer_verified,
            company_name='Wholesale Ltd',
            district='Bengaluru Urban'
        )

        # Unverified Buyer
        self.buyer_unverified = User.objects.create_user(
            email='unverified_buyer@test.com',
            password='password123',
            full_name='New Trader',
            role='buyer',
            is_verified=False
        )
        BuyerProfile.objects.create(
            user=self.buyer_unverified,
            company_name='New Trader Ltd',
            district='Bengaluru Urban'
        )

        # Product Listing (1000 kg available)
        self.listing = ProductListing.objects.create(
            farmer=self.farmer,
            product_name='Grade A Hybrid Tomato',
            crop='Tomato',
            quantity=1000.0,
            unit='kg',
            asking_price=25.0,
            quality_grade='A',
            quality_confidence=92,
            harvest_date='2026-11-12',
            district='Kolar',
            status='active'
        )

    def test_unverified_buyer_cannot_bid(self):
        self.client.force_authenticate(user=self.buyer_unverified)
        url = reverse('bid-list-create')
        data = {
            'listing_id': str(self.listing.id),
            'offered_price': 24.0,
            'quantity': 300.0,
            'message': 'Fast dispatch needed',
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_buyer_can_bid(self):
        self.client.force_authenticate(user=self.buyer_verified)
        url = reverse('bid-list-create')
        data = {
            'listing_id': str(self.listing.id),
            'offered_price': 24.0,
            'quantity': 400.0,
            'message': 'Ready for pickup',
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['status'], 'pending')
        self.assertEqual(res.data['current_responder'], 'farmer')

    def test_bid_exceeding_quantity_rejected(self):
        self.client.force_authenticate(user=self.buyer_verified)
        url = reverse('bid-list-create')
        data = {
            'listing_id': str(self.listing.id),
            'offered_price': 24.0,
            'quantity': 1500.0,  # Only 1000 available
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bid_acceptance_order_creation_and_partial_quantity(self):
        # 1. Buyer places bid of 400 kg
        bid = Bid.objects.create(
            listing=self.listing,
            farmer=self.farmer,
            buyer=self.buyer_verified,
            initiated_by='buyer',
            offered_price=24.0,
            quantity=400.0,
            status='pending',
            current_responder='farmer'
        )

        # Another bid of 700 kg (should get closed when 400 is accepted, because remaining 600 < 700)
        large_bid = Bid.objects.create(
            listing=self.listing,
            farmer=self.farmer,
            buyer=self.buyer_verified,
            initiated_by='buyer',
            offered_price=23.0,
            quantity=700.0,
            status='pending',
            current_responder='farmer'
        )

        # 2. Farmer accepts the 400 kg bid
        self.client.force_authenticate(user=self.farmer)
        accept_url = reverse('bid-accept', kwargs={'pk': str(bid.id)})
        res = self.client.post(accept_url, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check Order was created
        self.assertTrue(Order.objects.filter(accepted_bid=bid).exists())
        order = Order.objects.get(accepted_bid=bid)
        self.assertEqual(order.quantity, 400.0)
        self.assertEqual(order.total_amount, 9600.0)
        self.assertEqual(order.delivery_status, 'confirmed')

        # Check Listing remaining quantity: 1000 - 400 = 600 kg, status stays 'active'
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity, 600.0)
        self.assertEqual(self.listing.status, 'active')

        # Check large_bid was closed (rejected) because 700 kg > remaining 600 kg
        large_bid.refresh_from_db()
        self.assertEqual(large_bid.status, 'rejected')

    def test_listing_marked_sold_when_quantity_zero(self):
        # Buyer places bid for all 1000 kg
        bid = Bid.objects.create(
            listing=self.listing,
            farmer=self.farmer,
            buyer=self.buyer_verified,
            initiated_by='buyer',
            offered_price=25.0,
            quantity=1000.0,
            status='pending',
            current_responder='farmer'
        )

        self.client.force_authenticate(user=self.farmer)
        accept_url = reverse('bid-accept', kwargs={'pk': str(bid.id)})
        res = self.client.post(accept_url, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.quantity, 0.0)
        self.assertEqual(self.listing.status, 'sold')

    def test_prevent_double_acceptance(self):
        bid = Bid.objects.create(
            listing=self.listing,
            farmer=self.farmer,
            buyer=self.buyer_verified,
            initiated_by='buyer',
            offered_price=24.0,
            quantity=300.0,
            status='pending',
            current_responder='farmer'
        )

        self.client.force_authenticate(user=self.farmer)
        accept_url = reverse('bid-accept', kwargs={'pk': str(bid.id)})
        res1 = self.client.post(accept_url, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Second accept must fail
        res2 = self.client.post(accept_url, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
