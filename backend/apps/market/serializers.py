from rest_framework import serializers
from .models import MarketPrice, ContactMessage


class MarketPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = ['id', 'crop', 'state', 'district', 'market_name',
                  'price_per_kg', 'observation_date', 'data_source', 'is_demo_data']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
