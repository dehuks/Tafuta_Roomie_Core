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
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['message_id', 'conversation', 'sender', 'sender_name', 'message_text', 'sent_at', 'is_read']

class ConversationSerializer(serializers.ModelSerializer):
    # We will nest the last message to show a preview in the inbox
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['conversation_id', 'created_at', 'last_message']

    def get_last_message(self, obj):
        last_msg = obj.message_set.order_by('-sent_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
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