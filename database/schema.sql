-- =============================================================================
-- Eleos Database Schema
-- Build Specification from eleos_blueprint.md
-- =============================================================================

-- Enable required extensions for UUID generation and cryptographic hashing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. USERS & AUTH
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL CHECK (role IN ('donor', 'ngo_admin', 'reviewer', 'admin', 'volunteer')),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- =============================================================================
-- 2. NGO PROFILES
-- =============================================================================
CREATE TABLE IF NOT EXISTS ngo_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    registration_type VARCHAR(50), -- 'trust', 'society', 'section_8'
    registration_number VARCHAR(100),
    pan VARCHAR(10),
    darpan_id VARCHAR(50),        -- NGO Darpan unique ID
    fcra_registered BOOLEAN DEFAULT FALSE,
    fcra_number VARCHAR(50),
    tax_12a BOOLEAN DEFAULT FALSE,
    tax_80g BOOLEAN DEFAULT FALSE,
    state VARCHAR(100),
    district VARCHAR(100),
    city VARCHAR(100),
    founded_year INTEGER,
    website VARCHAR(255),
    description TEXT,
    logo_url TEXT,
    bank_account_name VARCHAR(255),
    bank_ifsc VARCHAR(20),
    bank_account_last4 VARCHAR(4), -- only last 4 digits stored
    verification_status VARCHAR(20) DEFAULT 'pending' CHECK (verification_status IN ('pending', 'verified', 'rejected', 'needs_info')),
    verified_at TIMESTAMPTZ,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ngo_profiles_user_id ON ngo_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_ngo_profiles_verification_status ON ngo_profiles(verification_status);
CREATE INDEX IF NOT EXISTS idx_ngo_profiles_darpan_id ON ngo_profiles(darpan_id);
CREATE INDEX IF NOT EXISTS idx_ngo_profiles_pan ON ngo_profiles(pan);

-- =============================================================================
-- 3. NGO DOCUMENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ngo_id UUID REFERENCES ngo_profiles(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN (
        'audit_report', 'registration_cert', 'pan_card',
        'fcra_cert', '12a_cert', '80g_cert', 'annual_report',
        'financial_statement', 'other'
    )),
    file_url TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,     -- SHA-256 of file
    file_size_bytes INTEGER,
    fiscal_year VARCHAR(10),            -- e.g., '2024-25'
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    ai_analysis JSONB,                  -- LLM extraction results
    verified BOOLEAN DEFAULT FALSE,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_documents_ngo_id ON documents(ngo_id);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_verified ON documents(verified);

-- =============================================================================
-- 4. CAMPAIGNS / PROJECTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ngo_id UUID REFERENCES ngo_profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'disaster_relief', 'education', 'healthcare',
        'nutrition', 'environment', 'marathon_fundraiser', 'other'
    )),
    location_state VARCHAR(100),
    location_district VARCHAR(100),
    location_country VARCHAR(100) DEFAULT 'India',
    target_amount DECIMAL(12,2) NOT NULL,
    raised_amount DECIMAL(12,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'INR',
    beneficiary_count INTEGER,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN (
        'draft', 'pending_review', 'active', 'paused',
        'completed', 'rejected', 'expired'
    )),
    safety_tier VARCHAR(20) DEFAULT 'open' CHECK (safety_tier IN (
        'open', 'trained_only', 'no_volunteers'
    )),
    is_disaster_relief BOOLEAN DEFAULT FALSE,
    start_date DATE,
    end_date DATE,
    cover_image_url TEXT,
    blockchain_project_hash VARCHAR(66), -- on-chain ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_campaigns_ngo_id ON campaigns(ngo_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_category ON campaigns(category);
CREATE INDEX IF NOT EXISTS idx_campaigns_is_disaster_relief ON campaigns(is_disaster_relief);

-- =============================================================================
-- 5. BUDGET LINE ITEMS
-- =============================================================================
CREATE TABLE IF NOT EXISTS budget_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    -- 'food', 'transport', 'medical', 'materials', 'labor', 'construction', 'admin', 'contingency', 'other'
    description TEXT NOT NULL,
    unit VARCHAR(50),              -- 'kg', 'person', 'day', 'unit', 'trip'
    unit_cost DECIMAL(10,2),
    quantity DECIMAL(10,2),
    total_cost DECIMAL(12,2) NOT NULL,
    -- benchmark comparison (filled by scoring engine)
    benchmark_unit_cost DECIMAL(10,2),
    benchmark_source VARCHAR(255),
    benchmark_source_url TEXT,
    benchmark_resolution VARCHAR(20) DEFAULT 'state' CHECK (benchmark_resolution IS NULL OR benchmark_resolution IN ('district', 'state', 'national', 'custom')),
    is_stale_adjusted BOOLEAN DEFAULT FALSE,
    cost_ratio DECIMAL(5,2),       -- submitted / benchmark
    flag VARCHAR(20) CHECK (flag IS NULL OR flag IN ('pass', 'warning', 'fail')),
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_budget_items_campaign_id ON budget_items(campaign_id);
CREATE INDEX IF NOT EXISTS idx_budget_items_category ON budget_items(category);

-- =============================================================================
-- 6. MILESTONES
-- =============================================================================
CREATE TABLE IF NOT EXISTS milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'evidence_submitted',
        'verified', 'overdue', 'failed'
    )),
    evidence_urls TEXT[],          -- array of file URLs
    evidence_hash VARCHAR(64),     -- SHA-256 of combined evidence
    blockchain_tx_hash VARCHAR(66),
    completed_at TIMESTAMPTZ,
    verified_by UUID REFERENCES users(id) ON DELETE SET NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_milestones_campaign_id ON milestones(campaign_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);

-- =============================================================================
-- 7. DONATIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS donations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    donor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    payment_method VARCHAR(20) CHECK (payment_method IS NULL OR payment_method IN ('upi', 'card', 'netbanking', 'crypto')),
    payment_gateway_order_id VARCHAR(100),
    payment_gateway_payment_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'initiated' CHECK (status IN (
        'initiated', 'processing', 'completed', 'failed', 'refunded'
    )),
    blockchain_tx_hash VARCHAR(66),
    blockchain_confirmed BOOLEAN DEFAULT FALSE,
    donor_message TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations(donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_campaign_id ON donations(campaign_id);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_blockchain_confirmed ON donations(blockchain_confirmed);
CREATE INDEX IF NOT EXISTS idx_donations_tx_hash ON donations(blockchain_tx_hash);

-- =============================================================================
-- 8. TRUSTABILITY SCORES
-- =============================================================================
CREATE TABLE IF NOT EXISTS trustability_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ngo_id UUID REFERENCES ngo_profiles(id) ON DELETE CASCADE,
    -- Individual dimension scores (0-100 each)
    identity_legal_score INTEGER,
    financial_transparency_score INTEGER,
    operational_performance_score INTEGER,
    governance_score INTEGER,
    data_completeness_score INTEGER,
    -- Aggregate
    overall_score INTEGER,
    overall_label VARCHAR(20) CHECK (overall_label IS NULL OR overall_label IN (
        'verified', 'partially_verified', 'unverified',
        'insufficient_data', 'high_risk', 'under_review'
    )),
    methodology_version VARCHAR(10) DEFAULT '1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    -- raw breakdown for explainability
    breakdown JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trustability_scores_ngo_id ON trustability_scores(ngo_id);
CREATE INDEX IF NOT EXISTS idx_trustability_scores_computed_at ON trustability_scores(computed_at DESC);

-- =============================================================================
-- 9. FEASIBILITY SCORES
-- =============================================================================
CREATE TABLE IF NOT EXISTS feasibility_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    -- Individual dimension scores (0-100 each)
    budget_realism_score INTEGER,
    cost_evidence_score INTEGER,
    beneficiary_consistency_score INTEGER,
    timeline_realism_score INTEGER,
    operational_capacity_score INTEGER,
    -- Aggregate
    overall_score INTEGER,
    overall_label VARCHAR(20) CHECK (overall_label IS NULL OR overall_label IN (
        'high', 'moderate', 'needs_evidence', 'low', 'very_low', 'under_review'
    )),
    context_adjustments JSONB,    -- disaster multiplier, rural premium, etc.
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    breakdown JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feasibility_scores_campaign_id ON feasibility_scores(campaign_id);
CREATE INDEX IF NOT EXISTS idx_feasibility_scores_computed_at ON feasibility_scores(computed_at DESC);

-- =============================================================================
-- 10. COST BENCHMARKS (curated regional cost dataset)
-- =============================================================================
CREATE TABLE IF NOT EXISTS cost_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,   -- 'food', 'transport', 'medical', etc.
    item VARCHAR(255) NOT NULL,       -- 'rice per kg', 'school uniform per set'
    unit VARCHAR(50) NOT NULL,        -- 'kg', 'meal', 'unit', 'day', 'trip'
    unit_cost_low DECIMAL(10,2),      -- range low
    unit_cost_mid DECIMAL(10,2),      -- median/typical
    unit_cost_high DECIMAL(10,2),     -- range high
    state VARCHAR(100),
    district VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    source_name VARCHAR(255),         -- 'PM POSHAN FY25-26', 'MOSPI CPI'
    source_url TEXT,
    effective_date DATE,
    expiry_date DATE,
    authority_type VARCHAR(50) DEFAULT 'statutory_order' CHECK (
        authority_type IS NULL OR authority_type IN ('statutory_order', 'cpi_basket', 'market_survey', 'historical_average')
    ),
    last_verified_at TIMESTAMPTZ,
    review_cycle_months INTEGER DEFAULT 12,
    disaster_multiplier DECIMAL(3,2) DEFAULT 1.0,
    rural_premium_pct DECIMAL(5,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cost_benchmarks_category ON cost_benchmarks(category);
CREATE INDEX IF NOT EXISTS idx_cost_benchmarks_item ON cost_benchmarks(item);
CREATE INDEX IF NOT EXISTS idx_cost_benchmarks_location ON cost_benchmarks(state, district);

-- =============================================================================
-- 11. VOLUNTEER OPPORTUNITIES
-- =============================================================================
CREATE TABLE IF NOT EXISTS volunteer_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    spots_total INTEGER,
    spots_filled INTEGER DEFAULT 0,
    safety_tier VARCHAR(20) DEFAULT 'open' CHECK (safety_tier IN ('open', 'trained_only', 'no_volunteers')),
    skills_required TEXT[],
    min_age INTEGER DEFAULT 18,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_volunteer_opps_campaign_id ON volunteer_opportunities(campaign_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_opps_safety ON volunteer_opportunities(safety_tier);

-- =============================================================================
-- 12. VOLUNTEER APPLICATIONS
-- =============================================================================
CREATE TABLE IF NOT EXISTS volunteer_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES volunteer_opportunities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'applied' CHECK (status IN (
        'applied', 'approved', 'rejected', 'completed', 'no_show'
    )),
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_vol_apps_opportunity_id ON volunteer_applications(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_vol_apps_user_id ON volunteer_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_vol_apps_status ON volunteer_applications(status);

-- =============================================================================
-- 13. VOLUNTEER HOURS + CREDENTIALS
-- =============================================================================
CREATE TABLE IF NOT EXISTS volunteer_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID UNIQUE REFERENCES volunteer_applications(id) ON DELETE CASCADE,
    hours_logged DECIMAL(5,1),
    ngo_confirmed BOOLEAN DEFAULT FALSE,
    ngo_confirmed_at TIMESTAMPTZ,
    blockchain_tx_hash VARCHAR(66),
    certificate_url TEXT,           -- generated PDF
    certificate_hash VARCHAR(64),   -- SHA-256 of certificate
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vol_cred_application_id ON volunteer_credentials(application_id);
CREATE INDEX IF NOT EXISTS idx_vol_cred_tx_hash ON volunteer_credentials(blockchain_tx_hash);

-- =============================================================================
-- 14. REVIEW QUEUE
-- =============================================================================
CREATE TABLE IF NOT EXISTS review_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('ngo', 'campaign')),
    entity_id UUID NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('critical', 'high', 'normal', 'low')),
    flags JSONB,                     -- array of flag reasons
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_review', 'resolved', 'escalated'
    )),
    reviewer_notes TEXT,
    decision VARCHAR(20) CHECK (decision IS NULL OR decision IN ('approved', 'rejected', 'needs_info', 'escalated')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_review_queue_status ON review_queue(status);
CREATE INDEX IF NOT EXISTS idx_review_queue_priority ON review_queue(priority);
CREATE INDEX IF NOT EXISTS idx_review_queue_entity ON review_queue(entity_type, entity_id);

