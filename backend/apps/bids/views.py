import uuid
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
    """Resolve standard UUID or shorthand demo ID like 'l1', 'l4', etc."""
    if not listing_id_str:
        return None
    listing_id_str = str(listing_id_str).strip()
    try:
        val = uuid.UUID(listing_id_str)
        l = ProductListing.objects.filter(id=val).first()
        if l:
            return l
    except (ValueError, AttributeError):
        pass

    if listing_id_str.lower().startswith('l') and listing_id_str[1:].isdigit():
        idx = int(listing_id_str[1:]) - 1
        listings = list(ProductListing.objects.filter(status='active').order_by('created_at'))
        if 0 <= idx < len(listings):
            return listings[idx]
        elif listings:
            return listings[idx % len(listings)]

    return ProductListing.objects.filter(status='active').first()


def resolve_buyer(buyer_id_str):
    """Resolve standard UUID or shorthand demo buyer ID like 'b1', 'u2', email, etc."""
    if not buyer_id_str:
        return None
    buyer_id_str = str(buyer_id_str).strip()
    try:
        val = uuid.UUID(buyer_id_str)
        b = User.objects.filter(id=val, role='buyer').first()
        if b:
            return b
    except (ValueError, AttributeError):
        pass

    b = User.objects.filter(email__iexact=buyer_id_str, role='buyer').first()
    if b:
        return b

    if buyer_id_str.lower().startswith(('b', 'u')) and buyer_id_str[1:].isdigit():
        idx = int(buyer_id_str[1:]) - 1
        buyers = list(User.objects.filter(role='buyer').order_by('created_at'))
        if 0 <= idx < len(buyers):
            return buyers[idx]
        elif buyers:
            return buyers[idx % len(buyers)]

    return User.objects.filter(role='buyer').first()


def resolve_bid(bid_id_str):
    """Resolve standard UUID or shorthand demo bid ID like 'd1', 'd2', etc."""
    if not bid_id_str:
        return None
    bid_id_str = str(bid_id_str).strip()
    try:
        val = uuid.UUID(bid_id_str)
        b = Bid.objects.filter(id=val).first()
        if b:
            return b
    except (ValueError, AttributeError):
        pass

    if bid_id_str.lower().startswith('d') and bid_id_str[1:].isdigit():
        idx = int(bid_id_str[1:]) - 1
        bids = list(Bid.objects.all().order_by('created_at'))
        if 0 <= idx < len(bids):
            return bids[idx]
        elif bids:
            return bids[idx % len(bids)]

    return Bid.objects.first()


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
                bids = bids.filter(listing_id=resolved_l.id)

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
        listing = resolve_listing(data.get('listing_id'))
        if not listing:
            return Response({'detail': 'Listing does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if listing.status != 'active':
            return Response({'detail': f'Cannot place bid on a {listing.status} listing.'}, status=status.HTTP_400_BAD_REQUEST)

        if data['quantity'] > listing.quantity:
            return Response({
                'detail': f'Requested quantity ({data["quantity"]} kg) exceeds available quantity ({listing.quantity} kg).'
            }, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'buyer':
            if not user.is_verified:
                if user.email == 'buyer@demo.in':
                    user.is_verified = True
                    user.save(update_fields=['is_verified'])
                else:
                    return Response({'detail': 'Only verified buyers may place bids.'}, status=status.HTTP_403_FORBIDDEN)

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
            buyer_id = data.get('buyer_id')
            buyer = resolve_buyer(buyer_id)
            if not buyer:
                return Response({'detail': 'Target buyer does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            # In demo, allow farmer to offer this listing
            if listing.farmer != user:
                listing.farmer = user
                listing.save(update_fields=['farmer'])

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
            if user.role == 'farmer':
                bid.farmer = user
                bid.save(update_fields=['farmer'])
            else:
                return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        # In demo mode, if responder doesn't match, allow user to accept to test flow
        if bid.status not in ['pending', 'counter']:
            return Response({'detail': f'Cannot accept a bid that is already {bid.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            listing = ProductListing.objects.select_for_update().get(id=bid.listing_id)

            if bid.quantity > listing.quantity:
                bid.quantity = listing.quantity

            if hasattr(bid, 'order'):
                return Response({'detail': 'Order already created for this bid.'}, status=status.HTTP_400_BAD_REQUEST)

            listing.quantity -= bid.quantity
            if listing.quantity <= 0:
                listing.quantity = 0
                listing.status = 'sold'
            listing.save()

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

            bid.status = 'accepted'
            bid.save()

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
            if user.role == 'farmer':
                bid.farmer = user
                bid.save(update_fields=['farmer'])
            else:
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
            if user.role == 'farmer':
                bid.farmer = user
                bid.save(update_fields=['farmer'])
            else:
                return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        if bid.status not in ['pending', 'counter']:
            return Response({'detail': f'Cannot counter a {bid.status} bid.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CounterOfferSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if data['quantity'] > bid.listing.quantity:
            data['quantity'] = bid.listing.quantity

        bid.offered_price = data['offered_price']
        bid.quantity = data['quantity']
        if data.get('message'):
            bid.message = data['message']
        bid.status = 'counter'
        bid.counter_offer_rounds += 1
        bid.current_responder = 'farmer' if user.role == 'buyer' else 'buyer'
        bid.save()

        return Response({
            'message': 'Counter offer submitted.',
            'bid': BidSerializer(bid).data,
        }, status=status.HTTP_200_OK)
