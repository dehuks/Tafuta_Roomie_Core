from rest_framework import serializers
from .models import User, UserPreferences, RoomListing, Match, Conversation, Message, Payment, Review

# --- 1. User & Auth Serializer ---
class UserSerializer(serializers.ModelSerializer):
    # Write_only ensures the password is never sent back in the API response (Security)
    password = serializers.CharField(write_only=True)
    

    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'phone_number', 'password', 'role', 'gender', 'is_verified']

    def create(self, validated_data):
        # We override create to use the manager's secure create_user method (hashes password)
        user = User.objects.create_user(**validated_data)
        return user

# --- 2. Preferences Serializer ---
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'
        # Don't make user read-only so it can be included in validated_data
    
    def create(self, validated_data):
        # Ensure user is set from context if not provided
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Don't allow changing the user
        validated_data.pop('user', None)
        return super().update(instance, validated_data)
# --- 3. Room Listing Serializer ---
class RoomListingSerializer(serializers.ModelSerializer):
    # Read_only field to show the owner's name instantly on the app card
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    
    class Meta:
        model = RoomListing
        fields = [
            'listing_id', 'owner', 'owner_name', 'title', 'description', 
            'city', 'rent_amount', 'room_type', 'available_from', 'created_at'
        ]

# --- 4. Match Serializer ---
class MatchSerializer(serializers.ModelSerializer):
    # Returns details of the person you matched with
    matched_user_name = serializers.CharField(source='matched_user.full_name', read_only=True)
    
    class Meta:
        model = Match
        fields = ['match_id', 'user', 'matched_user', 'matched_user_name', 'compatibility_score', 'match_status']

# --- 5. Messaging Serializers ---
class MessageSerializer(serializers.ModelSerializer):
    # Nest sender info so we can show their name/avatar in chat
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'sender_name', 'message_text', 'sent_at', 'is_read', 'is_me']

    def get_is_me(self, obj):
        # Returns True if the logged-in user sent this message
        request = self.context.get('request')
        if request and request.user:
            return obj.sender == request.user
        return False

class ConversationSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'other_participant', 'last_message', 'updated_at']

    def get_other_participant(self, obj):
        # Find the participant that is NOT the current user
        request = self.context.get('request')
        if request and request.user:
            other = obj.participants.exclude(pk=request.user.pk).first()
            if other:
                return UserSerializer(other).data
        return None

    def get_last_message(self, obj):
        last_msg = obj.messages.last() # Thanks to ordering in Meta
        if last_msg:
            return {
                'text': last_msg.message_text,
                'sent_at': last_msg.sent_at,
                'is_read': last_msg.is_read
            }
        return None

# --- 6. Payment Serializer ---
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['payment_id', 'user', 'listing', 'amount', 'payment_type', 'mpesa_reference', 'payment_status', 'paid_at']

# --- 7. Review Serializer ---
class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)

    class Meta:
        model = Review
        fields = ['review_id', 'reviewer', 'reviewer_name', 'reviewed_user', 'rating', 'comment', 'created_at']        