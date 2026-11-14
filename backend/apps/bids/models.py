import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.products.models import ProductListing


class Bid(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('counter', 'Counter Offer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='bids')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farmer_bids')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_bids')
    initiated_by = models.CharField(max_length=10, choices=ROLE_CHOICES)
    offered_price = models.FloatField(validators=[MinValueValidator(0.01)])
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_responder = models.CharField(max_length=10, choices=ROLE_CHOICES)
    message = models.TextField(blank=True, default='')
    delivery_preference = models.CharField(max_length=200, blank=True, default='')
    counter_offer_rounds = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bids'
        ordering = ['-created_at']

    def __str__(self):
        return f"Bid {self.id} on {self.listing.product_name} - ₹{self.offered_price}/kg ({self.status})"
