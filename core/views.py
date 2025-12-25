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
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Match, User, UserPreferences
from .serializers import MatchSerializer, UserSerializer



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

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        user = request.user
        data = request.data

        # 1. Get data from frontend
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        # 2. Validate inputs
        if not current_password or not new_password:
            return Response({'error': 'Both current and new passwords are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Check if old password matches
        if not user.check_password(current_password):
            return Response({'error': 'Invalid current password.'}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Set new password (hashes it automatically)
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)    

# 2. Listing ViewSet (Handles adding/viewing rooms)
class RoomListingViewSet(viewsets.ModelViewSet):
    queryset = RoomListing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RoomListingSerializer
    permission_classes = [permissions.AllowAny] # Open for now for testing

# 3. Preferences ViewSet
class UserPreferencesViewSet(viewsets.ModelViewSet):
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Admins can see all preferences, regular users only see their own
        if self.request.user.is_staff:
            return UserPreferences.objects.all()
        return UserPreferences.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create to handle upsert logic.
        If preferences exist, update them. Otherwise, create new.
        """
        # Determine which user we're creating/updating for
        # Use pk instead of id to work with any primary key field name
        if request.user.is_staff and 'user' in request.data:
            user_id = request.data['user']
        else:
            user_id = request.user.pk  # Changed from .id to .pk
        
        # Check if preferences already exist
        try:
            instance = UserPreferences.objects.get(user_id=user_id)
            # Preferences exist - update them
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            # Always explicitly set the user when updating
            if request.user.is_staff:
                serializer.save()
            else:
                serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserPreferences.DoesNotExist:
            # Preferences don't exist - create new
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            # IMPORTANT: Always explicitly set the user when creating
            if request.user.is_staff and 'user' in request.data:
                # Admin provided a user ID - use it
                user = User.objects.get(pk=request.data['user'])  # Changed to pk
                serializer.save(user=user)
            else:
                # Regular user or admin without user field - use current user
                serializer.save(user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        # Explicitly set user for updates too
        if self.request.user.is_staff and 'user' in self.request.data:
            user = User.objects.get(pk=self.request.data['user'])  # Changed to pk
            serializer.save(user=user)
        else:
            serializer.save(user=self.request.user)

# 4. Matching ViewSet
# --- HELPER: SCORING ALGORITHM ---
def calculate_compatibility(user_prefs, candidate_prefs):
    score = 0
    total_score = 0
    
    # 1. Cleanliness (Weight: 30%)
    # Logic: Exact match = 30, Adjacent (High vs Medium) = 15, Opposite = 0
    cleanliness_map = {'low': 1, 'medium': 2, 'high': 3}
    u_clean = cleanliness_map.get(user_prefs.cleanliness_level.lower(), 2)
    c_clean = cleanliness_map.get(candidate_prefs.cleanliness_level.lower(), 2)
    
    diff = abs(u_clean - c_clean)
    if diff == 0: score += 30
    elif diff == 1: score += 15
    # else diff is 2 (High vs Low) -> score += 0
    
    # 2. Smoking (Weight: 20%)
    # Logic: Non-smokers usually hate smokers. Smokers might not care.
    if user_prefs.smoking == candidate_prefs.smoking:
        score += 20
    elif user_prefs.smoking and not candidate_prefs.smoking: 
        # I smoke, they don't. Compatibility depends on them, but let's say 0 for now.
        score += 0
    
    # 3. Sleep Schedule (Weight: 20%)
    if user_prefs.sleep_schedule == candidate_prefs.sleep_schedule:
        score += 20
        
    # 4. Guests (Weight: 15%)
    if user_prefs.guests_allowed == candidate_prefs.guests_allowed:
        score += 15
        
    # 5. Pets (Weight: 10%)
    if user_prefs.pets == candidate_prefs.pets:
        score += 10
        
    # 6. Interest Tags (Weight: 5%)
    # Simple overlap check
    if user_prefs.other_interests and candidate_prefs.other_interests:
        u_tags = set(x.strip().lower() for x in user_prefs.other_interests.split(','))
        c_tags = set(x.strip().lower() for x in candidate_prefs.other_interests.split(','))
        common = u_tags.intersection(c_tags)
        if len(common) > 0:
            score += 5

    return score

# --- VIEWSET ---
class MatchViewSet(viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Match.objects.all()

    def list(self, request, *args, **kwargs):
        current_user = request.user
        
        # 1. Get Current User Preferences
        try:
            my_prefs = current_user.preferences
        except UserPreferences.DoesNotExist:
            return Response({"detail": "Complete profile first."}, status=400)

        # 2. GET EVERYONE (Relaxed Filtering)
        # We only exclude the user themselves and admins. 
        # We DO NOT filter by City/Gender here anymore.
        candidate_prefs = UserPreferences.objects.select_related('user').exclude(user=current_user)

        ranked_matches = []
        
        for candidate_pref in candidate_prefs:
            candidate_user = candidate_pref.user
            if candidate_user.is_superuser or candidate_user.is_staff: continue

            # --- 3. CALCULATE SCORE (Standard Weights) ---
            base_score = calculate_compatibility(my_prefs, candidate_pref)
            
            # --- 4. APPLY "PENALTIES" INSTEAD OF FILTERING ---
            
            # City Penalty (Huge penalty if cities don't match, but still shown)
            if my_prefs.city and candidate_pref.city:
                if my_prefs.city.lower() != candidate_pref.city.lower():
                    base_score -= 50 # Push them to the bottom
            
            # Gender Penalty (If preference is set and doesn't match)
            if my_prefs.preferred_gender and my_prefs.preferred_gender != 'prefer_not_to_say':
                if candidate_user.gender != my_prefs.preferred_gender:
                    base_score -= 30 # Significant penalty

            # Ensure score stays between 0 and 100
            final_score = max(0, min(100, base_score))

            # --- 5. LOWER THRESHOLD ---
            # Show everyone with at least 10% compatibility (was 40%)
            if final_score >= 10:
                ranked_matches.append({
                    "match_id": f"temp_{candidate_user.user_id}",
                    "compatibility_score": final_score,
                    "match_status": "pending",
                    "user": UserSerializer(candidate_user).data 
                })

        # Sort: Highest score first
        ranked_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)

        return Response(ranked_matches)

# 5. Conversation ViewSet (Chat Inbox)
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.none()

    # 1. Only show my conversations
    def get_queryset(self):
        return self.request.user.conversations.all()

    # 2. "Start Chat" Logic
    @action(detail=False, methods=['post'])
    def start(self, request):
        target_user_id = request.data.get('user_id')
        current_user = request.user

        if not target_user_id:
            return Response({"error": "User ID required"}, status=400)

        # Check if chat already exists
        # We look for conversations where both users are participants
        existing_chat = Conversation.objects.filter(participants=current_user).filter(participants__pk=target_user_id).first()

        if existing_chat:
            return Response(ConversationSerializer(existing_chat, context={'request': request}).data)

        # Create new if none exists
        try:
            target_user = User.objects.get(pk=target_user_id)
            chat = Conversation.objects.create()
            chat.participants.add(current_user, target_user)
            return Response(ConversationSerializer(chat, context={'request': request}).data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404) 

# 6. Message ViewSet (Sending Texts)
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.none()

    def get_queryset(self):
        # Filter messages by conversation ID passed in URL params ?conversation=5
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            # Security: Ensure user is actually in this conversation
            return Message.objects.filter(
                conversation_id=conversation_id, 
                conversation__participants=self.request.user
            )
        return Message.objects.none()

    def perform_create(self, serializer):
        # Auto-set sender
        conversation = serializer.validated_data['conversation']
        if self.request.user not in conversation.participants.all():
            raise ValidationError("You are not part of this conversation")
        
        serializer.save(sender=self.request.user)
        
        # Update conversation timestamp
        conversation.save() # Updates 'updated_at' automatically
# 7. Payment ViewSet (M-Pesa)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    # add a custom action here like:
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