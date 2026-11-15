from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from .unified_views import (
    health_view,
    crop_disease_info_view,
    predict_crop_disease_view,
    predict_price_view,
    forecast_demand_view,
    explain_price_view,
    markets_view,
    model_metrics_view,
    serve_frontend,
)

urlpatterns = [
    # Django Built-in Admin Site
    path('django-admin/', admin.site.urls),

    # Core REST API Endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/ai/', include('apps.products.ai_urls')),
    path('api/bids/', include('apps.bids.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/admin/', include('apps.admin_api.urls')),
    path('api/buyers/', include('apps.users.buyer_urls')),

    # Unified Machine Learning & CNN Endpoints (Direct on same port)
    path('health', health_view, name='unified-health-no-slash'),
    path('health/', health_view, name='unified-health'),
    path('crop-disease-info', crop_disease_info_view, name='unified-crop-disease-info-no-slash'),
    path('crop-disease-info/', crop_disease_info_view, name='unified-crop-disease-info'),
    path('predict-crop-disease', predict_crop_disease_view, name='unified-predict-crop-disease-no-slash'),
    path('predict-crop-disease/', predict_crop_disease_view, name='unified-predict-crop-disease'),
    path('ai/crop-disease', predict_crop_disease_view, name='unified-ai-crop-disease'),
    path('predict-price', predict_price_view, name='unified-predict-price'),
    path('forecast-demand', forecast_demand_view, name='unified-forecast-demand'),
    path('explain-price', explain_price_view, name='unified-explain-price'),
    path('markets', markets_view, name='unified-markets'),
    path('model-metrics', model_metrics_view, name='unified-model-metrics'),

    # Media uploads
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),

    # Frontend Single-Server Serving (HTML pages, CSS, JS, Assets)
    path('', serve_frontend, name='frontend-root'),
    re_path(r'^(?P<path>.*)$', serve_frontend, name='frontend-pages'),
]
