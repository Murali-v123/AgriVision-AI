import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, FarmerProfile, BuyerProfile
from apps.products.models import ProductListing, QualityAssessment
from apps.bids.models import Bid
from apps.orders.models import Order
from apps.market.models import MarketPrice


class Command(BaseCommand):
    help = 'Seeds demonstration users, listings, bids, orders and market data for AgriVision AI'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting seed_demo_data...'))

        today = datetime.date(2026, 11, 14)
        def days_ago(n):
            return today - datetime.timedelta(days=n)

        coords = {
            'Bengaluru Urban': (12.97, 77.59),
            'Bengaluru Rural': (13.20, 77.71),
            'Mysuru': (12.30, 76.64),
            'Mandya': (12.52, 76.90),
            'Tumakuru': (13.34, 77.10),
            'Hassan': (13.00, 76.10),
            'Kolar': (13.14, 78.13),
            'Chikkaballapur': (13.43, 77.73),
            'Ramanagara': (12.72, 77.28),
            'Dharwad': (15.46, 75.01),
            'Davanagere': (14.47, 75.92),
            'Hosur': (12.74, 77.83),
            'Chennai': (13.08, 80.27),
            'Coimbatore': (11.00, 76.96),
        }

        with transaction.atomic():
            # 1. Admin
            admin_user, created = User.objects.get_or_create(
                email='admin@demo.in',
                defaults={
                    'full_name': 'Platform Admin',
                    'phone': '9000000000',
                    'role': 'admin',
                    'is_verified': True,
                    'account_status': 'active',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            admin_user.set_password('admin123')
            admin_user.save()

            # 2. Farmers
            farmers_data = [
                ('f1', 'Ramesh Kumar', 'ramesh@demo.in', '9800000001', 'Ramesh Vegetable Farm', 'Mulbagal', 'Mulbagal', 'Kolar', 'Karnataka', 6, True),
                ('f2', 'Lakshmi Devi', 'lakshmi@demo.in', '9800000002', 'Lakshmi Organic Farms', 'Gudibande', 'Gudibande', 'Chikkaballapur', 'Karnataka', 9, True),
                ('f3', 'Suresh Gowda', 'suresh@demo.in', '9800000003', 'Gowda Green Fields', 'Kunigal', 'Kunigal', 'Tumakuru', 'Karnataka', 12, True),
                ('f4', 'Anitha R', 'anitha@demo.in', '9800000004', 'Anitha Agro', 'Maddur', 'Maddur', 'Mandya', 'Karnataka', 4, True),
                ('f5', 'Mahesh B', 'mahesh@demo.in', '9800000005', 'Malnad Farms', 'Arsikere', 'Arsikere', 'Hassan', 'Karnataka', 5, False),
                ('f6', 'Venkatesh N', 'venkat@demo.in', '9800000006', 'Venkat Produce', 'Hunsur', 'Hunsur', 'Mysuru', 'Karnataka', 8, True),
                ('f7', 'Pushpa K', 'pushpa@demo.in', '9800000007', 'Pushpa Farm', 'Magadi', 'Magadi', 'Ramanagara', 'Karnataka', 3, True),
                ('f8', 'Basavaraj P', 'basava@demo.in', '9800000008', 'Basava Fields', 'Malur', 'Malur', 'Kolar', 'Karnataka', 7, True),
                ('f9', 'Savitha M', 'savitha@demo.in', '9800000009', 'Savitha Harvest', 'Chintamani', 'Chintamani', 'Chikkaballapur', 'Karnataka', 2, False),
                ('f10', 'Ravi Shankar', 'ravi@demo.in', '9800000010', 'Shankar Agri', 'Tiptur', 'Tiptur', 'Tumakuru', 'Karnataka', 10, True),
            ]

            farmer_objs = {}
            for tag, name, email, phone, farm, vil, city, dist, st, acres, ver in farmers_data:
                u, _ = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'full_name': name,
                        'phone': phone,
                        'role': 'farmer',
                        'is_verified': ver,
                        'account_status': 'active',
                    }
                )
                u.set_password('farmer123')
                u.is_verified = ver
                u.save()

                c = coords.get(dist, (None, None))
                FarmerProfile.objects.update_or_create(
                    user=u,
                    defaults={
                        'farm_name': farm,
                        'village': vil,
                        'city': city,
                        'district': dist,
                        'state': st,
                        'latitude': c[0],
                        'longitude': c[1],
                        'location_sharing_enabled': True,
                        'farm_size': acres,
                    }
                )
                farmer_objs[tag] = u

            # 3. Buyers
            buyers_data = [
                ('b1', 'FreshMart Wholesale', 'Priya Nair', 'buyer@demo.in', '9900000001', 'Wholesaler', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', ['Tomato', 'Onion'], True),
                ('b2', 'Bharat Fresh Foods', 'Arun Kumar', 'bharat@demo.in', '9900000002', 'Food Processor', 'Hosur', 'Hosur', 'Tamil Nadu', ['Tomato', 'Onion'], True),
                ('b3', 'Annapurna Processing', 'Meena S', 'annapurna@demo.in', '9900000003', 'Food Processor', 'Chennai', 'Chennai', 'Tamil Nadu', ['Tomato', 'Potato'], False),
                ('b4', 'GreenMart Wholesale', 'Kiran Rao', 'greenmart@demo.in', '9900000004', 'Wholesaler', 'Mysuru', 'Mysuru', 'Karnataka', ['Tomato'], True),
                ('b5', 'Fresh Foods Pvt Ltd', 'Sandeep J', 'freshfoods@demo.in', '9900000005', 'Food Processor', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', ['Tomato', 'Onion'], True),
                ('b6', 'Daily Basket', 'Rahul M', 'dailybasket@demo.in', '9900000006', 'Retailer', 'Mandya', 'Mandya', 'Karnataka', ['Tomato', 'Potato'], True),
                ('b7', 'Namma Kirana', 'Lata P', 'nammakirana@demo.in', '9900000007', 'Retailer', 'Tumakuru', 'Tumakuru', 'Karnataka', ['Onion', 'Potato'], True),
                ('b8', 'Hubballi Veg Hub', 'Iqbal K', 'hubballi@demo.in', '9900000008', 'Wholesaler', 'Hubballi', 'Dharwad', 'Karnataka', ['Potato'], False),
                ('b9', 'Coimbatore Fresh Mart', 'Selvi R', 'cbefresh@demo.in', '9900000009', 'Retailer', 'Coimbatore', 'Coimbatore', 'Tamil Nadu', ['Tomato'], True),
                ('b10', 'Davanagere Food Works', 'Manjunath H', 'davanagere@demo.in', '9900000010', 'Food Processor', 'Davanagere', 'Davanagere', 'Karnataka', ['Onion', 'Potato'], True),
            ]

            buyer_objs = {}
            for tag, comp, contact, email, phone, btype, city, dist, st, interests, ver in buyers_data:
                u, _ = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'full_name': comp,
                        'phone': phone,
                        'role': 'buyer',
                        'is_verified': ver,
                        'account_status': 'active',
                    }
                )
                u.set_password('buyer123')
                u.is_verified = ver
                u.save()

                c = coords.get(dist, (None, None))
                BuyerProfile.objects.update_or_create(
                    user=u,
                    defaults={
                        'company_name': comp,
                        'contact_person': contact,
                        'business_type': btype,
                        'city': city,
                        'district': dist,
                        'state': st,
                        'latitude': c[0],
                        'longitude': c[1],
                        'location_sharing_enabled': True,
                        'interested_crops': interests,
                    }
                )
                buyer_objs[tag] = u

            # 4. Quality Assessment
            qa1, _ = QualityAssessment.objects.get_or_create(
                farmer=farmer_objs['f1'],
                crop='Tomato',
                defaults={
                    'predicted_grade': 'A',
                    'confidence': 91,
                    'assessment_details': {
                        'uniformity': 88,
                        'defects': 3,
                        'brightness': 62,
                        'ripeness': 'Ripe (stage 4 of 6)',
                    },
                    'assessment_method': 'pixel_heuristic_demo',
                }
            )

            # 5. Listings
            listings_data = [
                ('l1', 'f1', 'Hybrid Tomato', 'Tomato', 1200, 24, 'A', 'active', 'Kolar', 2),
                ('l2', 'f1', 'Desi Onion', 'Onion', 800, 19, 'B', 'sold', 'Kolar', 5),
                ('l3', 'f2', 'Organic Tomato', 'Tomato', 600, 27, 'A', 'sold', 'Chikkaballapur', 1),
                ('l4', 'f2', 'Kufri Potato', 'Potato', 1500, 17, 'B', 'active', 'Chikkaballapur', 8),
                ('l5', 'f3', 'Round Tomato', 'Tomato', 900, 22, 'B', 'active', 'Tumakuru', 3),
                ('l6', 'f3', 'Red Onion', 'Onion', 1100, 21, 'A', 'paused', 'Tumakuru', 10),
                ('l7', 'f4', 'Cherry Tomato', 'Tomato', 300, 34, 'A', 'sold', 'Mandya', 1),
                ('l8', 'f4', 'Agria Potato', 'Potato', 1000, 18, 'C', 'active', 'Mandya', 12),
                ('l9', 'f5', 'Local Tomato', 'Tomato', 750, 20, 'C', 'active', 'Hassan', 4),
                ('l10', 'f5', 'Bellary Onion', 'Onion', 1300, 18, 'B', 'sold', 'Hassan', 15),
                ('l11', 'f6', 'Hybrid Tomato', 'Tomato', 1000, 25, 'A', 'active', 'Mysuru', 2),
                ('l12', 'f6', 'Kufri Jyoti Potato', 'Potato', 700, 16, 'B', 'active', 'Mysuru', 6),
                ('l13', 'f7', 'Country Tomato', 'Tomato', 500, 23, 'B', 'active', 'Ramanagara', 2),
                ('l14', 'f7', 'Nasik Onion', 'Onion', 900, 22, 'A', 'active', 'Ramanagara', 4),
                ('l15', 'f8', 'Plum Tomato', 'Tomato', 400, 29, 'A', 'active', 'Kolar', 1),
                ('l16', 'f8', 'Chips Grade Potato', 'Potato', 1200, 19, 'A', 'active', 'Kolar', 7),
                ('l17', 'f9', 'Sun Ripe Tomato', 'Tomato', 650, 26, 'A', 'active', 'Chikkaballapur', 2),
                ('l18', 'f9', 'Small Onion', 'Onion', 600, 15, 'C', 'withdrawn', 'Chikkaballapur', 20),
                ('l19', 'f10', 'Bulk Tomato', 'Tomato', 1400, 21, 'B', 'active', 'Tumakuru', 3),
                ('l20', 'f10', 'Bulk Potato', 'Potato', 2000, 15, 'C', 'active', 'Tumakuru', 9),
            ]

            listing_objs = {}
            for tag, f_tag, name, crop, qty, ask, grade, stat, dist, ago in listings_data:
                conf = 92 if grade == 'A' else (84 if grade == 'B' else 72)
                l, _ = ProductListing.objects.get_or_create(
                    farmer=farmer_objs[f_tag],
                    product_name=name,
                    crop=crop,
                    defaults={
                        'quantity': qty,
                        'unit': 'kg',
                        'asking_price': ask,
                        'quality_grade': grade,
                        'quality_confidence': conf,
                        'quality_assessment': qa1 if (f_tag == 'f1' and crop == 'Tomato') else None,
                        'harvest_date': days_ago(ago),
                        'district': dist,
                        'status': stat,
                    }
                )
                listing_objs[tag] = l

            # 6. Bids & Orders
            deals_data = [
                ('d1', 'l1', 'buyer', 25.0, 500, 'pending', 'buyer', None, False, 'b1'),
                ('d2', 'l1', 'buyer', 24.0, 300, 'counter', 'farmer', None, False, 'b2'),
                ('d3', 'l2', 'farmer', 19.5, 400, 'pending', 'farmer', None, False, 'b5'),
                ('d4', 'l3', 'buyer', 27.0, 200, 'accepted', 'buyer', 'dispatched', False, 'b1'),
                ('d5', 'l7', 'buyer', 34.0, 100, 'accepted', 'buyer', 'delivered', True, 'b6'),
                ('d6', 'l10', 'buyer', 18.0, 1300, 'accepted', 'buyer', 'confirmed', False, 'b7'),
                ('d7', 'l11', 'buyer', 22.0, 400, 'rejected', 'buyer', None, False, 'b4'),
                ('d8', 'l2', 'buyer', 19.5, 800, 'accepted', 'buyer', 'delivered', True, 'b2'),
                ('d9', 'l16', 'buyer', 19.0, 500, 'pending', 'buyer', None, False, 'b9'),
            ]

            for tag, l_tag, initiator, price, qty, stat, responder, stage, paid, b_tag in deals_data:
                listing = listing_objs[l_tag]
                buyer = buyer_objs[b_tag]
                farmer = listing.farmer

                bid, _ = Bid.objects.get_or_create(
                    listing=listing,
                    farmer=farmer,
                    buyer=buyer,
                    offered_price=price,
                    quantity=qty,
                    defaults={
                        'initiated_by': initiator,
                        'status': stat,
                        'current_responder': responder,
                        'message': 'Demonstration bid' if initiator == 'buyer' else 'Demonstration offer',
                        'counter_offer_rounds': 2 if stat == 'counter' else 1,
                    }
                )

                if stat == 'accepted' and stage:
                    Order.objects.get_or_create(
                        accepted_bid=bid,
                        defaults={
                            'listing': listing,
                            'farmer': farmer,
                            'buyer': buyer,
                            'agreed_price': price,
                            'quantity': qty,
                            'total_amount': round(price * qty, 2),
                            'delivery_status': stage,
                            'payment_status': 'paid' if paid else 'pending',
                        }
                    )

            # 7. Market Prices
            market_samples = [
                ('Tomato', 'Karnataka', 'Bengaluru Urban', 'Bengaluru APMC', 28.5, days_ago(1)),
                ('Tomato', 'Karnataka', 'Kolar', 'Kolar APMC', 26.0, days_ago(1)),
                ('Tomato', 'Tamil Nadu', 'Chennai', 'Chennai Koyambedu', 31.0, days_ago(1)),
                ('Onion', 'Karnataka', 'Bengaluru Urban', 'Bengaluru APMC', 21.0, days_ago(1)),
                ('Onion', 'Karnataka', 'Kolar', 'Kolar APMC', 20.0, days_ago(1)),
                ('Potato', 'Karnataka', 'Bengaluru Urban', 'Bengaluru APMC', 18.0, days_ago(1)),
                ('Potato', 'Karnataka', 'Hassan', 'Hassan APMC', 17.5, days_ago(1)),
            ]

            for crop, state, dist, mkt, price, obs_date in market_samples:
                MarketPrice.objects.get_or_create(
                    crop=crop,
                    state=state,
                    district=dist,
                    market_name=mkt,
                    observation_date=obs_date,
                    defaults={
                        'price_per_kg': price,
                        'data_source': 'AgriVision Demonstration Market Data Feed',
                        'is_demo_data': True,
                    }
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded all demonstration data!'))
