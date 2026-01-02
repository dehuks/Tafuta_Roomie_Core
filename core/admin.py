from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    User, RoomListing, ListingImage, Match, 
    Conversation, Message, UserPreferences, UserVerification
)

# --- CUSTOM ACTIONS ---
@admin.action(description='✅ Approve selected verifications')
def approve_verifications(modeladmin, request, queryset):
    for verification in queryset:
        # 1. Update the Verification Request
        verification.verification_status = 'approved'
        verification.verified_at = timezone.now()
        verification.save()
        
        # 2. Update the actual User Profile
        user = verification.user
        user.is_verified = True
        user.save()
    
    modeladmin.message_user(request, f"Successfully approved {queryset.count()} users.")

@admin.action(description='❌ Reject selected verifications')
def reject_verifications(modeladmin, request, queryset):
    for verification in queryset:
        verification.verification_status = 'rejected'
        verification.save()
    modeladmin.message_user(request, f"Rejected {queryset.count()} verification requests.")

# --- ADMIN CLASSES ---

class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status_badge', 'submitted_at', 'thumbnail')
    list_filter = ('verification_status', 'document_type', 'submitted_at')
    actions = [approve_verifications, reject_verifications]
    readonly_fields = ('submitted_at', 'verified_at', 'image_preview')

    # Show small image in list
    def thumbnail(self, obj):
        if obj.document_image:
            return format_html('<img src="{}" style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px;" />', obj.document_image.url)
        return "No Image"

    # Show large image in detail view
    def image_preview(self, obj):
        if obj.document_image:
            return format_html('<img src="{}" style="max-width: 400px; max-height: 400px;" />', obj.document_image.url)
        return "No Image"

    # Color-coded status
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.verification_status, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.verification_status.upper())
    
    status_badge.short_description = 'Status'

class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'phone_number', 'role', 'is_verified_badge')
    list_filter = ('role', 'is_verified', 'is_active', 'gender')
    search_fields = ('email', 'full_name', 'phone_number')
    
    def is_verified_badge(self, obj):
        return "✅" if obj.is_verified else "❌"
    is_verified_badge.short_description = 'Verified'

class RoomListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'rent_amount', 'city', 'is_active')
    list_filter = ('city', 'room_type', 'is_active')

# --- REGISTER MODELS ---
admin.site.register(User, UserAdmin)
admin.site.register(UserVerification, UserVerificationAdmin)
admin.site.register(RoomListing, RoomListingAdmin)
admin.site.register(ListingImage)
admin.site.register(Match)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(UserPreferences)