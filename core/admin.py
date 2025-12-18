from django.contrib import admin
from django.db.models import Count
from .models import User, RoomListing, Match, Payment, Review, Conversation, UserPreferences

# 1. User Analytics Admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'is_verified', 'date_joined_pretty')
    list_filter = ('role', 'is_verified', 'status', 'gender') # Sidebar filters
    search_fields = ('email', 'full_name', 'phone_number')
    ordering = ('-created_at',)
    
    # Analytics: Show how many listings each user has
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(listing_count=Count('listings'))

    def date_joined_pretty(self, obj):
        return obj.created_at.strftime("%d %b %Y")
    date_joined_pretty.short_description = 'Joined'

# 2. Listing Admin with Image Preview
@admin.register(RoomListing)
class RoomListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner_link', 'rent_amount', 'city', 'room_type', 'is_active')
    list_filter = ('city', 'room_type', 'is_active')
    search_fields = ('title', 'description', 'city')
    list_editable = ('is_active',) # Toggle activation directly from list
    
    def owner_link(self, obj):
        return obj.owner.full_name
    owner_link.short_description = 'Landlord'

# 3. Matches Admin
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'matched_user', 'compatibility_score', 'match_status')
    list_filter = ('match_status',)
    search_fields = ('user__email', 'matched_user__email')

# 4. Payment Admin (Crucial for Verification)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('mpesa_reference', 'user', 'amount', 'payment_status', 'paid_at')
    list_filter = ('payment_status', 'payment_type')
    search_fields = ('mpesa_reference', 'user__email')
    readonly_fields = ('mpesa_reference', 'amount', 'payment_type') # Prevent tampering

# Register others simply
admin.site.register(Review)
admin.site.register(Conversation)
admin.site.register(UserPreferences)