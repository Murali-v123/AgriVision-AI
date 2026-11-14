import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.products.models import ProductListing
from apps.bids.models import Bid


class Order(models.Model):
    DELIVERY_STATUS = [
        ('confirmed', 'Confirmed'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accepted_bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='order')
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='orders')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='farmer_orders')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_orders')
    agreed_price = models.FloatField(validators=[MinValueValidator(0.01)])
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    total_amount = models.FloatField(validators=[MinValueValidator(0.01)])
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS, default='confirmed')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} for {self.listing.product_name} - ₹{self.total_amount}"


class SavedProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_products')
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='saved_by_buyers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'
        unique_together = ('buyer', 'listing')

    def __str__(self):
        return f"{self.buyer.email} saved {self.listing.product_name}"


class SavedFarmer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_farmers')
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_by_buyers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'
        unique_together = ('buyer', 'farmer')

    def __str__(self):
        return f"{self.buyer.email} saved farmer {self.farmer.email}"
