from django.urls import path
from .views import BuyerListView, BuyerNearbyView, BuyerDetailView

urlpatterns = [
    path('', BuyerListView.as_view(), name='buyer-list'),
    path('nearby/', BuyerNearbyView.as_view(), name='buyer-nearby'),
    path('<uuid:pk>/', BuyerDetailView.as_view(), name='buyer-detail'),
]
