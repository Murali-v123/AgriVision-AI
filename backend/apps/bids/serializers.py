from rest_framework import serializers
from .models import Bid
from apps.products.serializers import ProductListingSerializer


class BidSerializer(serializers.ModelSerializer):
    listing_detail = serializers.SerializerMethodField()
    farmer_name = serializers.CharField(source='farmer.full_name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    buyer_company = serializers.SerializerMethodField()

    class Meta:
        model = Bid
        fields = [
            'id', 'listing', 'listing_detail', 'farmer', 'farmer_name',
            'buyer', 'buyer_name', 'buyer_company', 'initiated_by',
            'offered_price', 'quantity', 'status', 'current_responder',
            'message', 'delivery_preference', 'counter_offer_rounds',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'farmer', 'buyer', 'status', 'current_responder',
            'counter_offer_rounds', 'created_at', 'updated_at'
        ]

    def get_listing_detail(self, obj):
        return {
            'id': str(obj.listing.id),
            'name': obj.listing.product_name,
            'crop': obj.listing.crop,
            'asking_price': obj.listing.asking_price,
            'available_qty': obj.listing.quantity,
            'quality_grade': obj.listing.quality_grade,
            'district': obj.listing.district,
            'status': obj.listing.status,
            'image': obj.listing.image.url if obj.listing.image else None,
        }

    def get_buyer_company(self, obj):
        if hasattr(obj.buyer, 'buyer_profile'):
            return obj.buyer.buyer_profile.company_name
        return obj.buyer.full_name


class BidCreateSerializer(serializers.Serializer):
    listing_id = serializers.CharField(max_length=100)
    offered_price = serializers.FloatField(min_value=0.01)
    quantity = serializers.FloatField(min_value=0.01)
    message = serializers.CharField(required=False, allow_blank=True, default='')
    delivery_preference = serializers.CharField(required=False, allow_blank=True, default='')
    buyer_id = serializers.CharField(max_length=100, required=False)  # When farmer initiates offer to a buyer


class CounterOfferSerializer(serializers.Serializer):
    offered_price = serializers.FloatField(min_value=0.01)
    quantity = serializers.FloatField(min_value=0.01)
    message = serializers.CharField(required=False, allow_blank=True, default='')
