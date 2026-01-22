from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Max
from .models import (User,
 RoomListing,
  Match, 
  UserPreferences, 
  Conversation, 
  Message, 
  Payment, 
  Review, 
  UserVerification
  ) 
from .serializers import (
    UserSerializer, RoomListingSerializer, MatchSerializer, 
    UserPreferencesSerializer, ConversationSerializer, 
    MessageSerializer, PaymentSerializer, ReviewSerializer, UserVerificationSerializer
)
from .notifications import send_push_notification 

# --- HELPER: SCORING ALGORITHM ---
def calculate_compatibility(user_prefs, candidate_prefs):
    score = 0
    
    # 1. Cleanliness (Weight: 30%)
    cleanliness_map = {'low': 1, 'medium': 2, 'high': 3}
    u_clean = cleanliness_map.get(user_prefs.cleanliness_level.lower(), 2)
    c_clean = cleanliness_map.get(candidate_prefs.cleanliness_level.lower(), 2)
    
    diff = abs(u_clean - c_clean)
    if diff == 0: score += 30
    elif diff == 1: score += 15
    
    # 2. Smoking (Weight: 20%)
    if user_prefs.smoking == candidate_prefs.smoking:
        score += 20
    elif user_prefs.smoking and not candidate_prefs.smoking: 
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
    if user_prefs.other_interests and candidate_prefs.other_interests:
        u_tags = set(x.strip().lower() for x in user_prefs.other_interests.split(','))
        c_tags = set(x.strip().lower() for x in candidate_prefs.other_interests.split(','))
        common = u_tags.intersection(c_tags)
        if len(common) > 0:
            score += 5

    return score

# 1. User ViewSet
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        user = request.user
        data = request.data

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'Both current and new passwords are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'Invalid current password.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)    

# 2. Listing ViewSet
class RoomListingViewSet(viewsets.ModelViewSet):
    queryset = RoomListing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RoomListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

# 3. Preferences ViewSet
class UserPreferencesViewSet(viewsets.ModelViewSet):
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserPreferences.objects.all()
        return UserPreferences.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.is_staff and 'user' in request.data:
            user_id = request.data['user']
        else:
            user_id = request.user.pk
        
        try:
            instance = UserPreferences.objects.get(user_id=user_id)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            if request.user.is_staff:
                serializer.save()
            else:
                serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserPreferences.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            if request.user.is_staff and 'user' in request.data:
                user = User.objects.get(pk=request.data['user'])
                serializer.save(user=user)
            else:
                serializer.save(user=request.user)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        if self.request.user.is_staff and 'user' in self.request.data:
            user = User.objects.get(pk=self.request.data['user'])
            serializer.save(user=user)
        else:
            serializer.save(user=self.request.user)

#4. Match ViewSet
class MatchViewSet(viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 1. Required for Router
    queryset = Match.objects.all()

    # 2. Filter: Only show MY matches (Requests sent to me OR by me)
    def get_queryset(self):
        return Match.objects.filter(
            Q(user=self.request.user) | Q(matched_user=self.request.user)
        )

    # 3. Create Logic: This handles the "Connect" button
    def perform_create(self, serializer):
        target_user_id = self.request.data.get('matched_user')
        
        if not target_user_id:
            raise serializers.ValidationError({"matched_user": "This field is required."})

        # Check for duplicates
        if Match.objects.filter(
            Q(user=self.request.user, matched_user_id=target_user_id) |
            Q(user_id=target_user_id, matched_user=self.request.user)
        ).exists():
            raise serializers.ValidationError({"detail": "Request already sent."})

        # Save with manually calculated fields
        serializer.save(
            user=self.request.user,
            matched_user_id=target_user_id,
            match_status='pending',
            compatibility_score=85 
        )

    def perform_update(self, serializer):
        # Because 'match_status' is read-only in the serializer, 
        # we must manually pull it from the request and save it.
        status_update = self.request.data.get('match_status')
        
        if status_update:
            # Force the update
            serializer.instance.match_status = status_update
            serializer.instance.save()
        else:
            super().perform_update(serializer)
                

    # 4. Recommendation Logic (The Algorithm)
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        current_user = request.user
        try:
            my_prefs = current_user.preferences
        except UserPreferences.DoesNotExist:
            return Response({"detail": "Complete profile first."}, status=400)

        candidate_prefs = UserPreferences.objects.select_related('user').exclude(user=current_user)
        ranked_matches = []
        
        for candidate_pref in candidate_prefs:
            candidate_user = candidate_pref.user
            if candidate_user.is_superuser or candidate_user.is_staff: 
                continue
            
            # 🛑 STRICT GENDER FILTERING (Male-Male / Female-Female)
            if candidate_user.gender != current_user.gender:
                continue

            # Skip people I'm already matched with
            if Match.objects.filter(
                (Q(user=current_user) & Q(matched_user=candidate_user)) |
                (Q(user=candidate_user) & Q(matched_user=current_user))
            ).exists():
                continue

            # Calculate Score (Simplified for brevity)
            base_score = calculate_compatibility(my_prefs, candidate_pref)
            
            # City penalty
            if my_prefs.city and candidate_pref.city:
                if my_prefs.city.lower() != candidate_pref.city.lower():
                    base_score -= 50

            final_score = max(0, min(100, base_score))

            if final_score >= 10:
                ranked_matches.append({
                    "match_id": f"temp_{candidate_user.user_id}",
                    "compatibility_score": final_score,
                    "match_status": "recommended",
                    "user": UserSerializer(candidate_user).data 
                })

        ranked_matches.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return Response(ranked_matches)

# 5. Conversation ViewSet (FIXED)
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.all()  # Required for router registration

    def get_queryset(self):
        # Return conversations for current user, ordered by most recent activity
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            latest_message=Max('messages__sent_at')
        ).order_by('-latest_message')

    def get_serializer_context(self):
        # Ensure request context is passed to serializer
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['post'])
    def start(self, request):
        target_user_id = request.data.get('user_id')
        current_user = request.user

        if not target_user_id:
            return Response({"error": "User ID required"}, status=400)

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Check if chat already exists between these two users
        existing_chat = Conversation.objects.filter(
            participants=current_user
        ).filter(
            participants=target_user
        ).first()

        if existing_chat:
            serializer = self.get_serializer(existing_chat)
            return Response(serializer.data)

        # Create new conversation
        chat = Conversation.objects.create()
        chat.participants.add(current_user, target_user)
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 6. Message ViewSet (FIXED)
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.all()  # Required for router registration

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation')
        if conversation_id:
            # Security: Ensure user is in this conversation
            return Message.objects.filter(
                conversation_id=conversation_id, 
                conversation__participants=self.request.user
            ).select_related('sender').order_by('sent_at')
        return Message.objects.none()

    def get_serializer_context(self):
        # Pass request to serializer for is_me field
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # 1. Identify the recipient (it's a chat, so it's the OTHER person)
        conversation = message.conversation
        recipient = conversation.participants.exclude(user_id=self.request.user.user_id).first()
        
        if recipient and recipient.expo_push_token:
            # 2. Send Notification
            send_push_notification(
                token=recipient.expo_push_token,
                title=f"New message from {self.request.user.full_name}",
                body=message.message_text,
                data={"conversation_id": conversation.conversation_id}
            )

# 7. Payment ViewSet
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

# 8. Review ViewSet
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

# 9. Register View
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 9. Verification (Fixed)
class UserVerificationViewSet(viewsets.ModelViewSet):
    queryset = UserVerification.objects.all()
    serializer_class = UserVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserVerification.objects.all()
        return UserVerification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        verification = self.get_object()
        verification.verification_status = 'approved'
        verification.verified_at = timezone.now() 
        verification.save()
        user = verification.user
        user.is_verified = True
        user.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        verification = self.get_object()
        reason = request.data.get('reason', 'Document invalid')
        verification.verification_status = 'rejected'
        verification.rejection_reason = reason
        verification.save()
        return Response({'status': 'rejected'})