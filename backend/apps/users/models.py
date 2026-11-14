import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(
        max_length=10,
        choices=[('farmer', 'Farmer'), ('buyer', 'Buyer'), ('admin', 'Admin')]
    )
    is_verified = models.BooleanField(default=False)
    account_status = models.CharField(
        max_length=20,
        default='active',
        choices=[('active', 'Active'), ('suspended', 'Suspended')]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    objects = UserManager()

    class Meta:
        app_label = 'users'

    def __str__(self):
        return f"{self.email} ({self.role})"


class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=200)
    village = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Karnataka')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_sharing_enabled = models.BooleanField(default=True)
    farm_size = models.FloatField(default=0)  # acres

    class Meta:
        app_label = 'users'

    def __str__(self):
        return f"{self.farm_name} - {self.user.email}"


class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('Wholesaler', 'Wholesaler'),
            ('Retailer', 'Retailer'),
            ('Food Processor', 'Food Processor'),
            ('Exporter', 'Exporter'),
        ]
    )
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Karnataka')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_sharing_enabled = models.BooleanField(default=True)
    interested_crops = models.JSONField(default=list)

    class Meta:
        app_label = 'users'

    def __str__(self):
        return f"{self.company_name} - {self.user.email}"
