from django.urls import path
from .views import (
    AdminAnalyticsView, AdminUserListView, AdminUserVerifyView,
    AdminUserSuspendView, AdminUserReactivateView, AdminProductListView,
    AdminTransactionListView, AdminModelMonitoringView
)

urlpatterns = [
    path('analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('users/', AdminUserListView.as_view(), name='admin-users'),
    path('users/<uuid:pk>/verify/', AdminUserVerifyView.as_view(), name='admin-user-verify'),
    path('users/<uuid:pk>/suspend/', AdminUserSuspendView.as_view(), name='admin-user-suspend'),
    path('users/<uuid:pk>/reactivate/', AdminUserReactivateView.as_view(), name='admin-user-reactivate'),
    path('products/', AdminProductListView.as_view(), name='admin-products'),
    path('transactions/', AdminTransactionListView.as_view(), name='admin-transactions'),
    path('models/', AdminModelMonitoringView.as_view(), name='admin-models'),
]
