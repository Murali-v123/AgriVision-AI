from django.urls import path
from .views import MarketPriceListView, PriceRecommendationView, MarketDemandView, ContactMessageView

urlpatterns = [
    path('prices/', MarketPriceListView.as_view(), name='market-prices'),
    path('recommendations/', PriceRecommendationView.as_view(), name='market-recommendations'),
    path('demand/', MarketDemandView.as_view(), name='market-demand'),
    path('contact/', ContactMessageView.as_view(), name='market-contact'),
]
