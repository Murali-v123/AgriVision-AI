from rest_framework import serializers
from .models import ProductListing, QualityAssessment
from apps.users.serializers import UserProfileSerializer


class QualityAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityAssessment
        fields = ['id', 'farmer', 'image', 'crop', 'predicted_grade', 'confidence',
                  'assessment_details', 'assessment_method', 'created_at']
        read_only_fields = ['id', 'farmer', 'created_at']


class ProductListingSerializer(serializers.ModelSerializer):
    farmer_detail = serializers.SerializerMethodField()

    class Meta:
        model = ProductListing
        fields = [
            'id', 'farmer', 'farmer_detail', 'product_name', 'crop', 'image',
            'quantity', 'unit', 'asking_price', 'quality_grade', 'quality_confidence',
            'quality_assessment', 'harvest_date', 'district', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'farmer', 'created_at', 'updated_at']

    def get_farmer_detail(self, obj):
        f = obj.farmer
        farm_name = f.full_name
        if hasattr(f, 'farmer_profile'):
            farm_name = f.farmer_profile.farm_name or f.full_name
        return {
            'id': str(f.id),
            'name': f.full_name,
            'farm_name': farm_name,
            'phone': f.phone,
            'is_verified': f.is_verified,
            'district': f.farmer_profile.district if hasattr(f, 'farmer_profile') else obj.district,
            'state': f.farmer_profile.state if hasattr(f, 'farmer_profile') else 'Karnataka',
        }


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductListing
        fields = [
            'product_name', 'crop', 'image', 'quantity', 'unit',
            'asking_price', 'quality_grade', 'quality_confidence',
            'quality_assessment', 'harvest_date', 'district', 'status'
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_asking_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Asking price must be greater than zero.")
        return value
