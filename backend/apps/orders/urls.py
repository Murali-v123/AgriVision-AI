from django.urls import path
from .views import OrderListView, OrderDetailView, OrderDispatchView, OrderDeliverView, OrderPaymentStatusView

urlpatterns = [
    path('', OrderListView.as_view(), name='order-list'),
    path('<str:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<str:pk>/dispatch/', OrderDispatchView.as_view(), name='order-dispatch'),
    path('<str:pk>/deliver/', OrderDeliverView.as_view(), name='order-deliver'),
    path('<str:pk>/payment-status/', OrderPaymentStatusView.as_view(), name='order-payment-status'),
]
