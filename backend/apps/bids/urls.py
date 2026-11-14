from django.urls import path
from .views import BidListCreateView, BidDetailView, BidAcceptView, BidRejectView, BidCounterView

urlpatterns = [
    path('', BidListCreateView.as_view(), name='bid-list-create'),
    path('<str:pk>/', BidDetailView.as_view(), name='bid-detail'),
    path('<str:pk>/accept/', BidAcceptView.as_view(), name='bid-accept'),
    path('<str:pk>/reject/', BidRejectView.as_view(), name='bid-reject'),
    path('<str:pk>/counter/', BidCounterView.as_view(), name='bid-counter'),
]
