# core/views.py
from rest_framework import viewsets, permissions
from .models import User, RoomListing, Match, UserPreferences
from .serializers import UserSerializer, RoomListingSerializer, MatchSerializer, UserPreferencesSerializer
from .models import Conversation, Message, Payment, Review
from .serializers import ConversationSerializer, MessageSerializer, PaymentSerializer, ReviewSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action



# 1. User ViewSet (Handles Registration & Profile)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # This line overrides the global "IsAuthenticated" setting just for this view
    permission_classes = [permissions.AllowAny]
    # Add this action!
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

# 2. Listing ViewSet (Handles adding/viewing rooms)
class RoomListingViewSet(viewsets.ModelViewSet):
    queryset = RoomListing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RoomListingSerializer
    permission_classes = [permissions.AllowAny] # Open for now for testing

# 3. Preferences ViewSet
class UserPreferencesViewSet(viewsets.ModelViewSet):
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferencesSerializer

# 4. Matching ViewSet
class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

# 5. Conversation ViewSet (Chat Inbox)
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    # In a real app, filter this to only show conversations the logged-in user belongs to
    queryset = Conversation.objects.all() 

# 6. Message ViewSet (Sending Texts)
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

# 7. Payment ViewSet (M-Pesa)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    # Later we will add a custom action here like:
    # @action(detail=False, methods=['post'])
    # def initiate_stk_push(self, request): ...

# 8. Review ViewSet
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer    

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            