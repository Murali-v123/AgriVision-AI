from django.urls import path
from .views import BidListCreateView, BidDetailView, BidAcceptView, BidRejectView, BidCounterView

urlpatterns = [
    path('', BidListCreateView.as_view(), name='bid-list-create'),
    path('<uuid:pk>/', BidDetailView.as_view(), name='bid-detail'),
    path('<uuid:pk>/accept/', BidAcceptView.as_view(), name='bid-accept'),
    path('<uuid:pk>/reject/', BidRejectView.as_view(), name='bid-reject'),
    path('<uuid:pk>/counter/', BidCounterView.as_view(), name='bid-counter'),
]
