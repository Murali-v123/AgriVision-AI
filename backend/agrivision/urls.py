from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from .frontend_views import serve_frontend

urlpatterns = [
    # Django Built-in Admin moved to django-admin/ to avoid conflict with frontend /admin/ portal
    path('django-admin/', admin.site.urls),
    
    # REST API endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/ai/', include('apps.products.ai_urls')),
    path('api/bids/', include('apps.bids.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/market/', include('apps.market.urls')),
    path('api/admin/', include('apps.admin_api.urls')),
    path('api/buyers/', include('apps.users.buyer_urls')),
]

# Media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Frontend SPA / HTML page routing (catches root /, login.html, farmer/*, buyer/*, admin/*, assets/*)
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_frontend, name='frontend'),
]
