from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    RoomListingViewSet, 
    UserPreferencesViewSet,
    MatchViewSet, 
    ConversationViewSet, 
    MessageViewSet,
    PaymentViewSet, 
    ReviewViewSet, 
    RegisterView,
    UserVerificationViewSet
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'listings', RoomListingViewSet)
router.register(r'preferences', UserPreferencesViewSet)
router.register(r'matches', MatchViewSet)
router.register(r'conversations', ConversationViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'verifications', UserVerificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]