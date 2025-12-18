# roommate_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Authentication Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Documentation Views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Core App Views
from core.views import (
    UserViewSet,
    RoomListingViewSet,
    MatchViewSet,
    UserPreferencesViewSet,
    RegisterView,ConversationViewSet, MessageViewSet, PaymentViewSet, ReviewViewSet 
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'listings', RoomListingViewSet)
router.register(r'matches', MatchViewSet)
router.register(r'preferences', UserPreferencesViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 1. Clean Auth Endpoints ---
    # Sign Up -> POST /api/register/
    path('api/register/', RegisterView.as_view(), name='register'),

    # Login -> POST /api/login/
    path('api/login/', TokenObtainPairView.as_view(), name='login'),

    # Refresh Token -> POST /api/refresh/
    path('api/refresh/', TokenRefreshView.as_view(), name='refresh'),

    # --- 2. General API Routes ---
    # e.g. /api/listings/ or /api/matches/
    path('api/', include(router.urls)),

    # --- 3. Documentation ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]