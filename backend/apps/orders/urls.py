from django.urls import path
from .views import OrderListView, OrderDetailView, OrderDispatchView, OrderDeliverView, OrderPaymentStatusView

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('<uuid:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:pk>/dispatch/', OrderDispatchView.as_view(), name='order-dispatch'),
    path('<uuid:pk>/deliver/', OrderDeliverView.as_view(), name='order-deliver'),
    path('<uuid:pk>/payment-status/', OrderPaymentStatusView.as_view(), name='order-payment-status'),
]
