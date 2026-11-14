from django.urls import path
from .views import ProductListCreateView, ProductDetailView

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('listings/', ProductListCreateView.as_view(), name='product-listings'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
