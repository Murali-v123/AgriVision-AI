from rest_framework import serializers
from .models import Order, SavedProduct, SavedFarmer
from apps.products.serializers import ProductListingSerializer


class OrderSerializer(serializers.ModelSerializer):
    listing_name = serializers.CharField(source='listing.product_name', read_only=True)
    crop = serializers.CharField(source='listing.crop', read_only=True)
    farmer_name = serializers.CharField(source='farmer.full_name', read_only=True)
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    buyer_company = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'accepted_bid', 'listing', 'listing_name', 'crop',
            'farmer', 'farmer_name', 'buyer', 'buyer_name', 'buyer_company',
            'agreed_price', 'quantity', 'total_amount', 'delivery_status',
            'payment_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'accepted_bid', 'listing', 'farmer', 'buyer',
            'agreed_price', 'quantity', 'total_amount', 'created_at', 'updated_at'
        ]

    def get_buyer_company(self, obj):
        if hasattr(obj.buyer, 'buyer_profile'):
            return obj.buyer.buyer_profile.company_name
        return obj.buyer.full_name


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['confirmed', 'dispatched', 'delivered'], required=False)
    payment_status = serializers.ChoiceField(choices=['pending', 'completed'], required=False)


class SavedProductSerializer(serializers.ModelSerializer):
    listing_detail = ProductListingSerializer(source='listing', read_only=True)

    class Meta:
        model = SavedProduct
        fields = ['id', 'buyer', 'listing', 'listing_detail', 'created_at']
        read_only_fields = ['id', 'buyer', 'created_at']
