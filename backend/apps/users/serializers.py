from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, FarmerProfile, BuyerProfile


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = ['farm_name', 'village', 'city', 'district', 'state',
                  'latitude', 'longitude', 'location_sharing_enabled', 'farm_size']


class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = ['company_name', 'contact_person', 'business_type', 'city',
                  'district', 'state', 'latitude', 'longitude',
                  'location_sharing_enabled', 'interested_crops']


class UserProfileSerializer(serializers.ModelSerializer):
    farmer_profile = FarmerProfileSerializer(read_only=True)
    buyer_profile = BuyerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'role', 'is_verified',
                  'account_status', 'created_at', 'farmer_profile', 'buyer_profile']
        read_only_fields = ['id', 'email', 'role', 'created_at']


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=['farmer', 'buyer'])
    # Farmer fields
    farm_name = serializers.CharField(required=False, allow_blank=True)
    village = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True, default='Karnataka')
    farm_size = serializers.FloatField(required=False, default=0)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    # Buyer fields
    company_name = serializers.CharField(required=False, allow_blank=True)
    contact_person = serializers.CharField(required=False, allow_blank=True)
    business_type = serializers.ChoiceField(
        choices=['Wholesaler', 'Retailer', 'Food Processor', 'Exporter'],
        required=False
    )
    city = serializers.CharField(required=False, allow_blank=True)
    interested_crops = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )

    def validate(self, data):
        role = data.get('role')
        if role == 'farmer':
            if not data.get('farm_name'):
                raise serializers.ValidationError({'farm_name': 'Farm name is required for farmers'})
            if not data.get('district'):
                raise serializers.ValidationError({'district': 'District is required for farmers'})
        elif role == 'buyer':
            if not data.get('company_name'):
                raise serializers.ValidationError({'company_name': 'Company name is required for buyers'})
            if not data.get('district'):
                raise serializers.ValidationError({'district': 'District is required for buyers'})
        return data

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        role = validated_data['role']
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone', ''),
            role=role,
        )
        if role == 'farmer':
            FarmerProfile.objects.create(
                user=user,
                farm_name=validated_data.get('farm_name', ''),
                village=validated_data.get('village', ''),
                city=validated_data.get('city', ''),
                district=validated_data.get('district', ''),
                state=validated_data.get('state', 'Karnataka'),
                farm_size=validated_data.get('farm_size', 0),
                latitude=validated_data.get('latitude'),
                longitude=validated_data.get('longitude'),
            )
        elif role == 'buyer':
            BuyerProfile.objects.create(
                user=user,
                company_name=validated_data.get('company_name', ''),
                contact_person=validated_data.get('contact_person', ''),
                business_type=validated_data.get('business_type', 'Wholesaler'),
                city=validated_data.get('city', ''),
                district=validated_data.get('district', ''),
                state=validated_data.get('state', 'Karnataka'),
                latitude=validated_data.get('latitude'),
                longitude=validated_data.get('longitude'),
                interested_crops=validated_data.get('interested_crops', []),
            )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if user.account_status == 'suspended':
            raise serializers.ValidationError('Account is suspended. Contact support.')
        data['user'] = user
        return data


class BuyerListSerializer(serializers.ModelSerializer):
    buyer_profile = BuyerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'is_verified', 'buyer_profile']
