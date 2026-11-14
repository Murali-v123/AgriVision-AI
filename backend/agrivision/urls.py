from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/ai/', include('apps.products.ai_urls')),
    path('api/bids/', include('apps.bids.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/admin/', include('apps.admin_api.urls')),
    path('api/buyers/', include('apps.users.buyer_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
