from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from PIL import Image
import io

from .models import ProductListing, QualityAssessment
from .serializers import ProductListingSerializer, ProductCreateSerializer, QualityAssessmentSerializer


def assess_produce_image(image_file):
    """
    Quality assessment heuristic based on RGB pixel analysis.
    Labels result clearly as 'pixel_heuristic_demo' to never claim false certification.
    """
    img = Image.open(image_file).convert('RGB').resize((64, 64))
    pixels = list(img.getdata())
    produce = [(r, g, b) for r, g, b in pixels if r + g + b <= 560]
    if not produce:
        raise ValueError("No produce detected in image")

    n = len(produce)
    brightness_vals = [0.3 * r + 0.59 * g + 0.11 * b for r, g, b in produce]
    rg_vals = [r - g for r, g, b in produce]
    mean_L = sum(brightness_vals) / n
    mean_rg = sum(rg_vals) / n
    variance_L = sum((x - mean_L) ** 2 for x in brightness_vals) / n
    variance_rg = sum((x - mean_rg) ** 2 for x in rg_vals) / n
    sd_L = variance_L ** 0.5
    sd_rg = variance_rg ** 0.5

    dark_count = sum(1 for L in brightness_vals if L < 0.6 * mean_L)
    uniformity = max(0, min(100, round(100 - (sd_L * 0.8 + sd_rg * 0.4))))
    defects = round(dark_count / n * 100)
    brightness = round(mean_L)

    grade = 'A' if uniformity >= 75 and defects <= 8 else 'B' if uniformity >= 50 and defects <= 12 else 'C'
    confidence = max(60, min(96, round(uniformity * 0.9 + 8)))
    ripeness = 'Ripe (stage 4 of 6)' if mean_rg > 100 else 'Turning (stage 3 of 6)' if mean_rg > 40 else 'Green (stage 2 of 6)'

    return {
        'grade': grade,
        'confidence': confidence,
        'details': {
            'uniformity': uniformity,
            'defects': defects,
            'brightness': brightness,
            'ripeness': ripeness,
        },
        'method': 'pixel_heuristic_demo',
    }


class ProductListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = ProductListing.objects.select_related('farmer', 'farmer__farmer_profile').all()

        # Farmer filtering own listings vs general browsing
        user = request.user if request.user.is_authenticated else None
        my_only = request.query_params.get('my') == 'true' or request.query_params.get('farmer') == 'me'
        if my_only and user and user.role == 'farmer':
            queryset = queryset.filter(farmer=user)
        else:
            status_param = request.query_params.get('status')
            if status_param and status_param != 'all':
                queryset = queryset.filter(status=status_param)
            elif not (user and (user.role == 'admin' or my_only)):
                queryset = queryset.filter(status='active')

        # Filters
        crop = request.query_params.get('crop')
        if crop:
            queryset = queryset.filter(crop__iexact=crop)

        district = request.query_params.get('district')
        if district:
            queryset = queryset.filter(district__iexact=district)

        grade = request.query_params.get('grade') or request.query_params.get('quality_grade')
        if grade:
            queryset = queryset.filter(quality_grade__iexact=grade)

        min_price = request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(asking_price__gte=float(min_price))
            except ValueError:
                pass

        max_price = request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(asking_price__lte=float(max_price))
            except ValueError:
                pass

        search = request.query_params.get('search') or request.query_params.get('q')
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(crop__icontains=search) |
                Q(district__icontains=search)
            )

        serializer = ProductListingSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role not in ['farmer', 'admin']:
            return Response({'detail': 'Only farmers can create listings.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            listing = serializer.save(farmer=request.user)
            output_serializer = ProductListingSerializer(listing)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def resolve_listing(pk):
    try:
        return ProductListing.objects.select_related('farmer', 'farmer__farmer_profile').get(id=pk)
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
    key = str(pk).lower()
    if key in demo_map:
        email, name = demo_map[key]
        return ProductListing.objects.select_related('farmer', 'farmer__farmer_profile').filter(farmer__email=email, product_name=name).first()
    return None


class ProductDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        listing = resolve_listing(pk)
        if not listing:
            return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductListingSerializer(listing)
        return Response(serializer.data)

    def patch(self, request, pk):
        listing = resolve_listing(pk)
        if not listing:
            return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)

        if listing.farmer != request.user and request.user.role != 'admin':
            return Response({'detail': 'You cannot edit another farmer\'s listing.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductCreateSerializer(listing, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ProductListingSerializer(listing).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        listing = resolve_listing(pk)
        if not listing:
            return Response({'detail': 'Listing not found.'}, status=status.HTTP_404_NOT_FOUND)

        if listing.farmer != request.user and request.user.role != 'admin':
            return Response({'detail': 'You cannot delete another farmer\'s listing.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if there are active accepted orders
        if listing.orders.filter(delivery_status__in=['confirmed', 'dispatched']).exists():
            return Response({'detail': 'Cannot delete listing with active orders. Mark as withdrawn instead.'}, status=status.HTTP_400_BAD_REQUEST)

        listing.delete()
        return Response({'message': 'Listing deleted successfully.'}, status=status.HTTP_200_OK)


class QualityAssessmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('image')
        crop = request.data.get('crop', 'Tomato')

        if not image_file:
            return Response({'detail': 'An image file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response({'detail': 'Image file size must be less than 10MB.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = assess_produce_image(image_file)
        except Exception as e:
            return Response({'detail': f'Assessment failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Save assessment
        image_file.seek(0)
        assessment = QualityAssessment.objects.create(
            farmer=request.user,
            image=image_file,
            crop=crop,
            predicted_grade=result['grade'],
            confidence=result['confidence'],
            assessment_details=result['details'],
            assessment_method=result['method'],
        )

        serializer = QualityAssessmentSerializer(assessment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
