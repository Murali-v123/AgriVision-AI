import math
from datetime import date
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import MarketPrice, ContactMessage
from .serializers import MarketPriceSerializer, ContactMessageSerializer

CROP_BASE = {'Tomato': 28.0, 'Onion': 21.0, 'Potato': 18.0}
DEMAND_IDX = {
    'Tomato': {'value': 82, 'label': 'High'},
    'Onion': {'value': 58, 'label': 'Medium'},
    'Potato': {'value': 41, 'label': 'Low'},
}
MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def calculate_current_price(crop, district):
    base = CROP_BASE.get(crop, 20.0)
    f = 0.97 + ((len(district or '')) % 8) * 0.01
    return round(base * f, 1)


def generate_series(crop, district, months=12):
    base = CROP_BASE.get(crop, 20.0)
    s = len(district or '') * 0.37 + len(crop)
    raw = []
    for i in range(months):
        k = months - 1 - i
        m = (10 - k + 120) % 12
        val = base * (1 + 0.14 * math.sin(i / 2.1 + s) + 0.03 * math.cos(i * 1.7))
        raw.append({'label': MON[m], 'v': val})

    now = calculate_current_price(crop, district)
    last = raw[-1]['v']
    return [{'label': p['label'], 'value': round(p['v'] * now / last, 1)} for p in raw]


def calculate_recommended_price(crop, district):
    hist = generate_series(crop, district, 12)[-3:]
    avg_3m = sum(p['value'] for p in hist) / 3.0
    return round(avg_3m * 1.04, 1)


class MarketPriceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = MarketPrice.objects.all()
        crop = request.query_params.get('crop')
        state = request.query_params.get('state')
        district = request.query_params.get('district')
        market_name = request.query_params.get('market')

        if crop:
            queryset = queryset.filter(crop__iexact=crop)
        if state:
            queryset = queryset.filter(state__iexact=state)
        if district:
            queryset = queryset.filter(district__iexact=district)
        if market_name:
            queryset = queryset.filter(market_name__icontains=market_name)

        serializer = MarketPriceSerializer(queryset[:100], many=True)
        return Response({
            'count': queryset.count(),
            'is_demo_data': True,
            'data_source': 'Simulated demonstration mandi series (labeled demo data)',
            'results': serializer.data,
        })


class PriceRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        crop = request.query_params.get('crop', 'Tomato')
        district = request.query_params.get('district', 'Kolar')
        state = request.query_params.get('state', 'Karnataka')
        months = int(request.query_params.get('months', 12))

        cur = calculate_current_price(crop, district)
        rec = calculate_recommended_price(crop, district)
        hist_series = generate_series(crop, district, months)
        demand = DEMAND_IDX.get(crop, {'value': 50, 'label': 'Medium'})

        return Response({
            'crop': crop,
            'district': district,
            'state': state,
            'current_price_per_kg': cur,
            'recommended_price_per_kg': rec,
            'demand_indicator': demand,
            'series': hist_series,
            'is_demo_data': True,
            'data_source': 'AgriVision Market Intelligence Demonstration Rule (1.04x last 3-month avg, not live mandi forecast)',
        })


class MarketDemandView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        crop = request.query_params.get('crop')
        if crop:
            demand = DEMAND_IDX.get(crop, {'value': 50, 'label': 'Medium'})
            return Response({
                'crop': crop,
                'demand': demand,
                'is_demo_data': True,
            })
        return Response({
            'demands': DEMAND_IDX,
            'is_demo_data': True,
        })


class ContactMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Message received. Platform team has recorded your contact request.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
