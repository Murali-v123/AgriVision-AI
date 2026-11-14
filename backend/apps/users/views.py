from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
import math

from .models import User, FarmerProfile, BuyerProfile
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    UserProfileSerializer, BuyerListSerializer,
    FarmerProfileSerializer, BuyerProfileSerializer
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            profile_serializer = UserProfileSerializer(user)
            return Response({
                'message': 'Registration successful',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'tokens': tokens,
                'user': profile_serializer.data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            profile_serializer = UserProfileSerializer(user)
            return Response({
                'message': 'Login successful',
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'tokens': tokens,
                'user': profile_serializer.data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        data = request.data

        # Update basic user fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        user.save()

        # Update profile
        if user.role == 'farmer':
            profile = getattr(user, 'farmer_profile', None)
            if profile:
                farmer_fields = ['farm_name', 'village', 'city', 'district', 'state',
                                 'latitude', 'longitude', 'location_sharing_enabled', 'farm_size']
                for field in farmer_fields:
                    if field in data:
                        setattr(profile, field, data[field])
                profile.save()
        elif user.role == 'buyer':
            profile = getattr(user, 'buyer_profile', None)
            if profile:
                buyer_fields = ['company_name', 'contact_person', 'business_type', 'city',
                                'district', 'state', 'latitude', 'longitude',
                                'location_sharing_enabled', 'interested_crops']
                for field in buyer_fields:
                    if field in data:
                        setattr(profile, field, data[field])
                profile.save()

        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


# ---- Buyer views ----

class BuyerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = User.objects.filter(role='buyer', is_active=True).select_related('buyer_profile')
        business_type = request.query_params.get('business_type')
        if business_type:
            queryset = queryset.filter(buyer_profile__business_type=business_type)
        serializer = BuyerListSerializer(queryset, many=True)
        return Response(serializer.data)


class BuyerNearbyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = User.objects.filter(role='buyer', is_active=True).select_related('buyer_profile')
        user = request.user
        farmer_lat = None
        farmer_lon = None
        if user.role == 'farmer' and hasattr(user, 'farmer_profile'):
            farmer_lat = user.farmer_profile.latitude
            farmer_lon = user.farmer_profile.longitude

        buyers = list(queryset)
        if farmer_lat and farmer_lon:
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            def dist_key(b):
                p = getattr(b, 'buyer_profile', None)
                if p and p.latitude and p.longitude:
                    return haversine(farmer_lat, farmer_lon, p.latitude, p.longitude)
                return float('inf')

            buyers.sort(key=dist_key)

        serializer = BuyerListSerializer(buyers, many=True)
        return Response(serializer.data)


class BuyerDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            buyer = User.objects.select_related('buyer_profile').get(id=pk, role='buyer')
        except User.DoesNotExist:
            return Response({'detail': 'Buyer not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BuyerListSerializer(buyer)
        return Response(serializer.data)
