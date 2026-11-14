from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Sum, Count

from apps.users.models import User
from apps.users.serializers import UserProfileSerializer
from apps.products.models import ProductListing, QualityAssessment
from apps.products.serializers import ProductListingSerializer
from apps.bids.models import Bid
from apps.bids.serializers import BidSerializer
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer


class IsAdminUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser)
        )


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        total_users = User.objects.count()
        farmers_count = User.objects.filter(role='farmer').count()
        buyers_count = User.objects.filter(role='buyer').count()
        verified_users = User.objects.filter(is_verified=True).count()
        suspended_users = User.objects.filter(account_status='suspended').count()

        total_listings = ProductListing.objects.count()
        active_listings = ProductListing.objects.filter(status='active').count()
        sold_listings = ProductListing.objects.filter(status='sold').count()

        total_bids = Bid.objects.count()
        accepted_bids = Bid.objects.filter(status='accepted').count()

        total_orders = Order.objects.count()
        gmv_data = Order.objects.aggregate(total_gmv=Sum('total_amount'))
        total_gmv = gmv_data['total_gmv'] or 0.0

        delivered_orders = Order.objects.filter(delivery_status='delivered').count()
        paid_orders = Order.objects.filter(payment_status='paid').count()
        assessments_count = QualityAssessment.objects.count()

        return Response({
            'users': {
                'total': total_users,
                'farmers': farmers_count,
                'buyers': buyers_count,
                'verified': verified_users,
                'suspended': suspended_users,
            },
            'listings': {
                'total': total_listings,
                'active': active_listings,
                'sold': sold_listings,
            },
            'bids': {
                'total': total_bids,
                'accepted': accepted_bids,
            },
            'orders': {
                'total': total_orders,
                'total_gmv': round(total_gmv, 2),
                'delivered': delivered_orders,
                'paid': paid_orders,
            },
            'ai_quality': {
                'total_assessments_logged': assessments_count,
                'status': 'Active Pixel-Heuristic Engine',
                'active_model': 'Demonstration RGB Feature Heuristic (non-certified)',
            }
        })


class AdminUserListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        queryset = User.objects.select_related('farmer_profile', 'buyer_profile').all().order_by('-created_at')
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(account_status=status_param)

        serializer = UserProfileSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminUserVerifyView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = not user.is_verified
        user.save()

        return Response({
            'message': f"User {user.email} verification set to {user.is_verified}.",
            'user': UserProfileSerializer(user).data
        })


class AdminUserSuspendView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.account_status = 'suspended'
        user.save()

        return Response({
            'message': f"User {user.email} suspended.",
            'user': UserProfileSerializer(user).data
        })


class AdminUserReactivateView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.account_status = 'active'
        user.save()

        return Response({
            'message': f"User {user.email} reactivated.",
            'user': UserProfileSerializer(user).data
        })


class AdminProductListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        listings = ProductListing.objects.select_related('farmer', 'farmer__farmer_profile').all().order_by('-created_at')
        serializer = ProductListingSerializer(listings, many=True)
        return Response(serializer.data)


class AdminTransactionListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        orders = Order.objects.select_related('listing', 'farmer', 'buyer').all().order_by('-created_at')
        bids = Bid.objects.select_related('listing', 'farmer', 'buyer').all().order_by('-created_at')

        return Response({
            'orders': OrderSerializer(orders, many=True).data,
            'bids': BidSerializer(bids, many=True).data,
        })


class AdminModelMonitoringView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        assessments = QualityAssessment.objects.all()
        total_evals = assessments.count()
        grade_a = assessments.filter(predicted_grade='A').count()
        grade_b = assessments.filter(predicted_grade='B').count()
        grade_c = assessments.filter(predicted_grade='C').count()

        return Response({
            'engine_name': 'AgriVision AI Quality Inspector',
            'implementation': 'Deterministic RGB Pixel Analysis Heuristic (Demonstration Model)',
            'trained_weights_loaded': False,
            'deep_learning_backend': 'Ready for MobileNetV3 / ResNet-50 weights replacement',
            'metrics_disclaimer': 'All confidence scores and metrics are calculated via pixel distribution heuristic; no fabricated inference times or artificial deep-learning benchmarks are claimed.',
            'total_inspections': total_evals,
            'grade_distribution': {
                'A': grade_a,
                'B': grade_b,
                'C': grade_c,
            },
            'certification_statement': 'AgriVision AI produces marketplace grading recommendations, not official AGMARKNET certification.',
        })
