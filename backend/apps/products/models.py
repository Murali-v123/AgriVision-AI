import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class QualityAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quality_assessments')
    image = models.ImageField(upload_to='assessments/', null=True, blank=True)
    crop = models.CharField(max_length=50, default='Tomato')
    predicted_grade = models.CharField(max_length=5, choices=[('A', 'Grade A'), ('B', 'Grade B'), ('C', 'Grade C')])
    confidence = models.IntegerField(default=85)
    assessment_details = models.JSONField(default=dict)
    assessment_method = models.CharField(max_length=100, default='pixel_heuristic_demo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.crop} - Grade {self.predicted_grade} ({self.confidence}%) by {self.farmer.email}"


class ProductListing(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('sold', 'Sold'),
        ('withdrawn', 'Withdrawn'),
        ('hidden', 'Hidden'),
    ]
    CROP_CHOICES = [
        ('Tomato', 'Tomato'),
        ('Onion', 'Onion'),
        ('Potato', 'Potato'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    product_name = models.CharField(max_length=200)
    crop = models.CharField(max_length=50, choices=CROP_CHOICES)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])
    unit = models.CharField(max_length=20, default='kg')
    asking_price = models.FloatField(validators=[MinValueValidator(0.01)])
    quality_grade = models.CharField(max_length=5, choices=[('A', 'Grade A'), ('B', 'Grade B'), ('C', 'Grade C')])
    quality_confidence = models.IntegerField(default=85)
    quality_assessment = models.ForeignKey(QualityAssessment, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    harvest_date = models.DateField()
    district = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product_name} - {self.crop} ({self.quantity} {self.unit}) by {self.farmer.email}"
