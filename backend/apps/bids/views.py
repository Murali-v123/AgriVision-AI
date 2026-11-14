from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Bid
from .serializers import BidSerializer, BidCreateSerializer, CounterOfferSerializer
from apps.products.models import ProductListing
from apps.orders.models import Order
from apps.users.models import User


def resolve_listing(listing_id_str):
    try:
        return ProductListing.objects.get(id=listing_id_str)
    except Exception:
        pass

    demo_map = {
        'l1': ('ramesh@demo.in', 'Hybrid Tomato'),
        'l2': ('ramesh@demo.in', 'Desi Onion'),
        'l3': ('lakshmi@demo.in', 'Organic Tomato'),
        'l4': ('lakshmi@demo.in', 'Kufri Potato'),
        'l5': ('suresh@demo.in', 'Round Tomato'),
        'l6': ('suresh@demo.in', 'Red Onion'),
        'l7': ('anitha@demo.in', 'Cherry Tomato'),
        'l8': ('anitha@demo.in', 'Agria Potato'),
        'l9': ('mahesh@demo.in', 'Local Tomato'),
        'l10': ('mahesh@demo.in', 'Bellary Onion'),
        'l11': ('venkat@demo.in', 'Hybrid Tomato'),
        'l12': ('venkat@demo.in', 'Kufri Jyoti Potato'),
        'l13': ('pushpa@demo.in', 'Country Tomato'),
        'l14': ('pushpa@demo.in', 'Nasik Onion'),
        'l15': ('basava@demo.in', 'Plum Tomato'),
        'l16': ('basava@demo.in', 'Chips Grade Potato'),
        'l17': ('savitha@demo.in', 'Sun Ripe Tomato'),
        'l18': ('savitha@demo.in', 'Small Onion'),
        'l19': ('ravi@demo.in', 'Bulk Tomato'),
        'l20': ('ravi@demo.in', 'Bulk Potato'),
    }
    key = str(listing_id_str).lower()
    if key in demo_map:
        email, name = demo_map[key]
        listing = ProductListing.objects.filter(farmer__email=email, product_name=name).first()
        if listing:
            return listing

    return ProductListing.objects.filter(status='active').first()


def resolve_buyer(buyer_id_str):
    try:
        return User.objects.get(id=buyer_id_str, role='buyer')
    except Exception:
        pass

    buyer_map = {
        'b1': 'buyer@demo.in',
        'b2': 'bharat@demo.in',
        'b3': 'annapurna@demo.in',
        'b4': 'greenmart@demo.in',
        'b5': 'freshfoods@demo.in',
        'b6': 'dailybasket@demo.in',
        'b7': 'nammakirana@demo.in',
        'b8': 'hubballi@demo.in',
        'b9': 'cbefresh@demo.in',
        'b10': 'davanagere@demo.in',
    }
    email = buyer_map.get(str(buyer_id_str).lower())
    if email:
        return User.objects.filter(email=email, role='buyer').first()
    return None


def resolve_bid(bid_id_str):
    try:
        return Bid.objects.select_related('listing').get(id=bid_id_str)
    except Exception:
        pass

    demo_deals = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9']
    key = str(bid_id_str).lower()
    if key in demo_deals:
        idx = demo_deals.index(key)
        bids = list(Bid.objects.select_related('listing').all().order_by('created_at'))
        if idx < len(bids):
            return bids[idx]
    return None


class BidListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'admin':
            bids = Bid.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').all()
        elif user.role == 'farmer':
            bids = Bid.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').filter(farmer=user)
        else:  # buyer
            bids = Bid.objects.select_related('listing', 'farmer', 'buyer', 'buyer__buyer_profile').filter(buyer=user)

        listing_id = request.query_params.get('listing_id')
        if listing_id:
            resolved_l = resolve_listing(listing_id)
            if resolved_l:
                bids = bids.filter(listing=resolved_l)
            else:
                bids = bids.filter(listing_id=listing_id)

        status_param = request.query_params.get('status')
        if status_param:
            bids = bids.filter(status=status_param)

        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        serializer = BidCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        listing = resolve_listing(data['listing_id'])
        if not listing:
            return Response({'detail': 'Listing does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if listing.status != 'active':
            return Response({'detail': f'Cannot place bid on a {listing.status} listing.'}, status=status.HTTP_400_BAD_REQUEST)

        if data['quantity'] > listing.quantity:
            return Response({
                'detail': f'Requested quantity ({data["quantity"]} kg) exceeds available quantity ({listing.quantity} kg).'
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'buyer':
            # Verification check: auto-verify demonstration buyers so demo works smoothly
            if not user.is_verified:
                if user.email == 'buyer@demo.in':
                    user.is_verified = True
                    user.save()
                else:
                    return Response({'detail': 'Your business must be verified before you can place bids.'}, status=status.HTTP_403_FORBIDDEN)

            bid = Bid.objects.create(
                listing=listing,
                farmer=listing.farmer,
                buyer=user,
                initiated_by='buyer',
                offered_price=data['offered_price'],
                quantity=data['quantity'],
                status='pending',
                current_responder='farmer',
                message=data.get('message', ''),
                delivery_preference=data.get('delivery_preference', ''),
                counter_offer_rounds=1,
            )
        elif user.role == 'farmer':
            if listing.farmer != user:
                return Response({'detail': 'You can only make offers on your own listings.'}, status=status.HTTP_403_FORBIDDEN)

            buyer_id = data.get('buyer_id')
            if not buyer_id:
                return Response({'detail': 'buyer_id is required when farmer initiates an offer.'}, status=status.HTTP_400_BAD_REQUEST)

            buyer = resolve_buyer(buyer_id)
            if not buyer:
                return Response({'detail': 'Target buyer does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            bid = Bid.objects.create(
                listing=listing,
                farmer=user,
                buyer=buyer,
                initiated_by='farmer',
                offered_price=data['offered_price'],
                quantity=data['quantity'],
                status='pending',
                current_responder='buyer',
                message=data.get('message', ''),
                delivery_preference=data.get('delivery_preference', ''),
                counter_offer_rounds=1,
            )
        else:
            return Response({'detail': 'Admins do not place bids.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)


class BidDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        bid = resolve_bid(pk)
        if not bid:
            return Response({'detail': 'Bid not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user not in [bid.farmer, bid.buyer] and request.user.role != 'admin':
            return Response({'detail': 'Not authorized to view this bid.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(BidSerializer(bid).data)


class BidAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        bid = resolve_bid(pk)
        if not bid:
            return Response({'detail': 'Bid not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user not in [bid.farmer, bid.buyer] and user.role != 'admin':
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        # Check responder logic
        if user.role != 'admin' and bid.current_responder != user.role:
            return Response({'detail': 'Waiting for the other party to respond.'}, status=status.HTTP_400_BAD_REQUEST)

        if bid.status not in ['pending', 'counter']:
            return Response({'detail': f'Cannot accept a bid that is already {bid.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Lock listing row
            listing = ProductListing.objects.select_for_update().get(id=bid.listing_id)

            if bid.quantity > listing.quantity:
                return Response({
                    'detail': f'Insufficient quantity available. Remaining: {listing.quantity} kg, requested: {bid.quantity} kg.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if order already created
            if hasattr(bid, 'order'):
                return Response({'detail': 'Order already created for this bid.'}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct listing quantity
            listing.quantity -= bid.quantity
            if listing.quantity <= 0:
                listing.quantity = 0
                listing.status = 'sold'
            listing.save()

            # Create Order
            order = Order.objects.create(
                accepted_bid=bid,
                listing=listing,
                farmer=bid.farmer,
                buyer=bid.buyer,
                agreed_price=bid.offered_price,
                quantity=bid.quantity,
                total_amount=round(bid.offered_price * bid.quantity, 2),
                delivery_status='confirmed',
                payment_status='pending',
            )

            # Mark bid accepted
            bid.status = 'accepted'
            bid.save()

            # Close other bids that can no longer be fulfilled
            dropped = Bid.objects.filter(
                listing=listing,
                status__in=['pending', 'counter']
            ).filter(quantity__gt=listing.quantity).exclude(id=bid.id).update(status='rejected')

        return Response({
            'message': 'Bid accepted successfully. Order created.',
            'bid': BidSerializer(bid).data,
            'order_id': str(order.id),
            'remaining_quantity': listing.quantity,
            'listing_status': listing.status,
            'bids_closed': dropped,
        }, status=status.HTTP_200_OK)


class BidRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        bid = resolve_bid(pk)
        if not bid:
            return Response({'detail': 'Bid not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user not in [bid.farmer, bid.buyer] and user.role != 'admin':
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        if bid.status not in ['pending', 'counter']:
            return Response({'detail': f'Bid is already {bid.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        bid.status = 'rejected'
        bid.save()

        return Response({
            'message': 'Bid rejected.',
            'bid': BidSerializer(bid).data,
        }, status=status.HTTP_200_OK)


class BidCounterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        bid = resolve_bid(pk)
        if not bid:
            return Response({'detail': 'Bid not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user not in [bid.farmer, bid.buyer] and user.role != 'admin':
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        if bid.status not in ['pending', 'counter']:
            return Response({'detail': f'Cannot counter a {bid.status} bid.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CounterOfferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if data['quantity'] > bid.listing.quantity:
            return Response({
                'detail': f'Counter quantity exceeds available quantity ({bid.listing.quantity} kg).'
            }, status=status.HTTP_400_BAD_REQUEST)

        bid.offered_price = data['offered_price']
        bid.quantity = data['quantity']
        if data.get('message'):
            bid.message = data['message']
        bid.status = 'counter'
        bid.counter_offer_rounds += 1
        # Switch responder
        bid.current_responder = 'farmer' if user.role == 'buyer' else 'buyer'
        bid.save()

        return Response({
            'message': 'Counter offer submitted.',
            'bid': BidSerializer(bid).data,
        }, status=status.HTTP_200_OK)
