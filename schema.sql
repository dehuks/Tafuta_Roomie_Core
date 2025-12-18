-- schema.sql
-- Find a Roommate System Database Schema
-- Optimized for PostgreSQL & Docker Initialization

-- 1. Create ENUM Types
-- We create these first as the tables depend on them.

CREATE TYPE gender_enum AS ENUM (
    'male',
    'female',
    'non_binary',
    'prefer_not_to_say'
);

-- Includes 'admin' role as discussed
CREATE TYPE user_role_enum AS ENUM (
    'seeker',
    'host',
    'both',
    'admin'
);

CREATE TYPE account_status_enum AS ENUM (
    'active',
    'suspended'
);

CREATE TYPE verification_type_enum AS ENUM (
    'national_id',
    'student_id',
    'social_media'
);

CREATE TYPE verification_status_enum AS ENUM (
    'pending',
    'approved',
    'rejected'
);

CREATE TYPE cleanliness_enum AS ENUM (
    'low',
    'medium',
    'high'
);

CREATE TYPE noise_enum AS ENUM (
    'low',
    'medium',
    'high'
);

CREATE TYPE sleep_enum AS ENUM (
    'day',
    'night',
    'flexible'
);

CREATE TYPE room_type_enum AS ENUM (
    'private',
    'shared',
    'bedsitter'
);

CREATE TYPE match_status_enum AS ENUM (
    'pending',
    'accepted',
    'rejected'
);

CREATE TYPE payment_type_enum AS ENUM (
    'deposit',
    'rent'
);

CREATE TYPE payment_status_enum AS ENUM (
    'pending',
    'successful',
    'failed'
);

-- 2. Create Tables

-- Users Table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    gender gender_enum NOT NULL,
    date_of_birth DATE,
    role user_role_enum NOT NULL DEFAULT 'seeker',
    is_verified BOOLEAN DEFAULT FALSE,
    status account_status_enum DEFAULT 'active',
    -- Essential for Django Admin compatibility (is_staff/is_superuser logic handled in code, but good to track)
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Verification
CREATE TABLE user_verification (
    verification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    verification_type verification_type_enum NOT NULL,
    document_reference VARCHAR(255),
    verification_status verification_status_enum DEFAULT 'pending',
    verified_at TIMESTAMP,

    CONSTRAINT fk_verification_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- User Preferences (For Matching)
CREATE TABLE user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    cleanliness_level cleanliness_enum,
    smoking BOOLEAN,
    pets BOOLEAN,
    noise_tolerance noise_enum,
    guests_allowed BOOLEAN,
    sleep_schedule sleep_enum,
    budget_min NUMERIC(10,2),
    budget_max NUMERIC(10,2),
    preferred_gender gender_enum,
    city VARCHAR(50),

    CONSTRAINT fk_preferences_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Room Listings
CREATE TABLE room_listings (
    listing_id SERIAL PRIMARY KEY,
    owner_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    city VARCHAR(50) NOT NULL,
    area VARCHAR(100),
    rent_amount NUMERIC(10,2) NOT NULL,
    deposit_amount NUMERIC(10,2),
    room_type room_type_enum NOT NULL,
    available_from DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_listing_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Listing Images
CREATE TABLE listing_images (
    image_id SERIAL PRIMARY KEY,
    listing_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_image_listing
        FOREIGN KEY (listing_id)
        REFERENCES room_listings(listing_id)
        ON DELETE CASCADE
);

-- Matches
CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    matched_user_id INT NOT NULL,
    compatibility_score NUMERIC(5,2),
    match_status match_status_enum DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_match_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_match_matched_user
        FOREIGN KEY (matched_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_match_pair UNIQUE (user_id, matched_user_id)
);

-- Conversations
CREATE TABLE conversations (
    conversation_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_message_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_message_sender
        FOREIGN KEY (sender_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- Payments (M-Pesa Integration)
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    listing_id INT NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    payment_type payment_type_enum NOT NULL,
    mpesa_reference VARCHAR(100) UNIQUE,
    payment_status payment_status_enum DEFAULT 'pending',
    paid_at TIMESTAMP,

    CONSTRAINT fk_payment_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_payment_listing
        FOREIGN KEY (listing_id)
        REFERENCES room_listings(listing_id)
        ON DELETE CASCADE
);

-- Reviews
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    reviewer_id INT NOT NULL,
    reviewed_user_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_review_reviewer
        FOREIGN KEY (reviewer_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_review_reviewed
        FOREIGN KEY (reviewed_user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_review UNIQUE (reviewer_id, reviewed_user_id)
);

-- 3. Indexes for Performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_listings_city ON room_listings(city);
CREATE INDEX idx_matches_score ON matches(compatibility_score);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_payments_status ON payments(payment_status);