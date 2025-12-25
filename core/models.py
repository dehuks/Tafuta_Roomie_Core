from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# --- 1. MANAGERS ---
class UserManager(BaseUserManager):
    def create_user(self, email, phone_number, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, full_name, password=None):
        user = self.create_user(email, phone_number, full_name, password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

# --- 2. ENUMS ---
class Role(models.TextChoices):
    SEEKER = 'seeker', 'Seeker'
    HOST = 'host', 'Host'
    BOTH = 'both', 'Both'
    ADMIN = 'admin', 'Admin'

class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    NON_BINARY = 'non_binary', 'Non Binary'
    PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer Not to Say'

class RoomType(models.TextChoices):
    PRIVATE = 'private', 'Private'
    SHARED = 'shared', 'Shared'
    BEDSITTER = 'bedsitter', 'Bedsitter'

# --- 3. MODELS ---

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=100)
    phone_number = models.CharField(unique=True, max_length=20)
    gender = models.CharField(max_length=20, choices=Gender.choices)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.SEEKER)
    is_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']

    class Meta:
        db_table = 'users'

class UserVerification(models.Model):
    verification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=50) # You can add choices here if needed
    document_reference = models.CharField(max_length=255, null=True, blank=True)
    verification_status = models.CharField(max_length=20, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_verification'

class UserPreferences(models.Model):
    preference_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    cleanliness_level = models.CharField(max_length=10, null=True)
    smoking = models.BooleanField(default=False)
    pets = models.BooleanField(default=False)
    noise_tolerance = models.CharField(max_length=10, null=True)
    guests_allowed = models.BooleanField(default=False)
    sleep_schedule = models.CharField(max_length=10, null=True)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    preferred_gender = models.CharField(max_length=20, choices=Gender.choices, null=True)
    city = models.CharField(max_length=50, null=True)
    other_interests = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'user_preferences'

class RoomListing(models.Model):
    listing_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=100)
    description = models.TextField()
    city = models.CharField(max_length=50)
    area = models.CharField(max_length=100, null=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    available_from = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'room_listings'

class ListingImage(models.Model):
    image_id = models.AutoField(primary_key=True)
    listing = models.ForeignKey(RoomListing, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'listing_images'

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_initiated')
    matched_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_received')
    compatibility_score = models.DecimalField(max_digits=5, decimal_places=2)
    match_status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'matches'
        unique_together = ('user', 'matched_user')

class Conversation(models.Model):
    conversation_id = models.AutoField(primary_key=True)
    # 👇 Crucial: Who is in this chat?
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    # 👇 Helps sort inbox by latest activity
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at'] 

class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'messages'
        ordering = ['sent_at'] # Oldest messages at top (like WhatsApp)

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(RoomListing, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20) # 'deposit' or 'rent'
    mpesa_reference = models.CharField(max_length=100, unique=True, null=True)
    payment_status = models.CharField(max_length=20, default='pending')
    paid_at = models.DateTimeField(null=True)

    class Meta:
        db_table = 'payments'

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField()
    comment = models.TextField(null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'reviews'
        unique_together = ('reviewer', 'reviewed_user')