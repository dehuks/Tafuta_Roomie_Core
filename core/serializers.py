# core/serializers.py
from rest_framework import serializers
from .models import (
    User, UserPreferences, RoomListing, Match, Conversation, 
    Message, Payment, Review, ListingImage, UserVerification
)

# --- 1. User & Auth Serializer ---
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    preferences = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'full_name', 'email', 'phone_number', 'password', 'role', 'gender', 'is_verified', 'preferences']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def get_preferences(self, obj):
        try:
            return UserPreferencesSerializer(obj.preferences).data
        except UserPreferences.DoesNotExist:
            return None

# --- 2. Preferences Serializer ---
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = '__all__'
    
    def create(self, validated_data):
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.pop('user', None)
        return super().update(instance, validated_data)

# --- 3. Image Serializer ---
class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['image_id', 'image_file', 'uploaded_at']

# --- 4. Room Listing Serializer ---
class RoomListingSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = RoomListing
        fields = [
            'listing_id', 'owner', 'owner_name', 
            'title', 'description', 'city', 'area', 
            'rent_amount', 'deposit_amount', 'room_type', 
            'available_from', 'images', 'uploaded_images', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at']

    def create(self, validated_data):
        images_data = validated_data.pop('uploaded_images', [])
        listing = RoomListing.objects.create(**validated_data)
        for image_data in images_data:
            ListingImage.objects.create(listing=listing, image_file=image_data)
        return listing

# --- 5. Match Serializer ---
class MatchSerializer(serializers.ModelSerializer):
    matched_user_name = serializers.CharField(source='matched_user.full_name', read_only=True)
    user = UserSerializer(read_only=True) 
    
    class Meta:
        model = Match
        fields = ['match_id', 'user', 'matched_user', 'matched_user_name', 'compatibility_score', 'match_status']

# --- 6. Messaging Serializers ---
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['message_id', 'conversation', 'sender', 'sender_name', 'message_text', 'sent_at', 'is_read', 'is_me']
        read_only_fields = ['message_id', 'sender', 'sender_name', 'sent_at', 'is_read', 'is_me']

    def get_is_me(self, obj):
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
        request = self.context.get('request')
        if request and request.user:
            other = obj.participants.exclude(pk=request.user.pk).first()
            if other:
                return UserSerializer(other).data
        return None

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'text': last_msg.message_text,
                'sent_at': last_msg.sent_at,
                'is_read': last_msg.is_read
            }
        return None

# --- 7. Payment & Review ---
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    class Meta:
        model = Review
        fields = '__all__'

# --- 8. Verification Serializer (FIXED) ---
class UserVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['verification_id', 'user', 'document_image', 'document_type', 'verification_status', 'submitted_at', 'rejection_reason']
        read_only_fields = ['user', 'verification_status', 'verified_at', 'rejection_reason', 'submitted_at']

    def create(self, validated_data):
        # 👇 This line is now correctly indented
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'user_id',
            'email',
            'full_name',
            'phone_number',
            'role',
            'is_verified',
        ]        