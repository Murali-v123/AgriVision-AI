import uuid
from django.db import models


class MarketPrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    crop = models.CharField(max_length=50)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    market_name = models.CharField(max_length=200)
    price_per_kg = models.FloatField()
    observation_date = models.DateField()
    data_source = models.CharField(max_length=200, default='demonstration')
    is_demo_data = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'market'
        ordering = ['-observation_date']

    def __str__(self):
        return f"{self.crop} at {self.market_name} ({self.district}): ₹{self.price_per_kg}/kg"


class ContactMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'market'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
