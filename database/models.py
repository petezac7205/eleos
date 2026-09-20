"""
Eleos Database Models (SQLAlchemy 2.0 ORM)
Matches the exact schema specified in eleos_blueprint.md
"""

import uuid
from datetime import datetime, date
from typing import List, Optional, Any, Dict
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, index=True)
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    # Relationships
    ngo_profile = relationship("NGOProfile", back_populates="user", uselist=False, foreign_keys="NGOProfile.user_id")
    donations = relationship("Donation", back_populates="donor")
    volunteer_applications = relationship("VolunteerApplication", back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('donor', 'ngo_admin', 'reviewer', 'admin', 'volunteer')", name="chk_user_role"),
    )


class NGOProfile(Base):
    __tablename__ = "ngo_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    registration_type = Column(String(50), nullable=True)  # 'trust', 'society', 'section_8'
    registration_number = Column(String(100), nullable=True)
    pan = Column(String(10), nullable=True, index=True)
    darpan_id = Column(String(50), nullable=True, index=True)
    fcra_registered = Column(Boolean, default=False, server_default=text("FALSE"))
    fcra_number = Column(String(50), nullable=True)
    tax_12a = Column(Boolean, default=False, server_default=text("FALSE"))
    tax_80g = Column(Boolean, default=False, server_default=text("FALSE"))
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    bank_account_name = Column(String(255), nullable=True)
    bank_ifsc = Column(String(20), nullable=True)
    bank_account_last4 = Column(String(4), nullable=True)
    verification_status = Column(String(20), default="pending", server_default=text("'pending'"), index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="ngo_profile")
    verifier = relationship("User", foreign_keys=[verified_by])
    documents = relationship("Document", back_populates="ngo", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="ngo", cascade="all, delete-orphan")
    trustability_scores = relationship("TrustabilityScore", back_populates="ngo", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("verification_status IN ('pending', 'verified', 'rejected', 'needs_info')", name="chk_ngo_verification_status"),
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    ngo_id = Column(UUID(as_uuid=True), ForeignKey("ngo_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(50), nullable=False, index=True)
    file_url = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_size_bytes = Column(Integer, nullable=True)
    fiscal_year = Column(String(10), nullable=True)  # e.g. '2024-25'
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    ai_analysis = Column(JSONB, nullable=True)  # LLM extraction results
    verified = Column(Boolean, default=False, server_default=text("FALSE"), index=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    ngo = relationship("NGOProfile", back_populates="documents")
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        CheckConstraint(
            "doc_type IN ('audit_report', 'registration_cert', 'pan_card', 'fcra_cert', '12a_cert', '80g_cert', 'annual_report', 'financial_statement', 'other')",
            name="chk_doc_type"
        ),
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    ngo_id = Column(UUID(as_uuid=True), ForeignKey("ngo_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    location_state = Column(String(100), nullable=True)
    location_district = Column(String(100), nullable=True)
    location_country = Column(String(100), default="India", server_default=text("'India'"))
    target_amount = Column(Numeric(12, 2), nullable=False)
    raised_amount = Column(Numeric(12, 2), default=0.00, server_default=text("0"))
    currency = Column(String(3), default="INR", server_default=text("'INR'"))
    beneficiary_count = Column(Integer, nullable=True)
    status = Column(String(20), default="draft", server_default=text("'draft'"), index=True)
    safety_tier = Column(String(20), default="open", server_default=text("'open'"))
    is_disaster_relief = Column(Boolean, default=False, server_default=text("FALSE"), index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    cover_image_url = Column(Text, nullable=True)
    blockchain_project_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    ngo = relationship("NGOProfile", back_populates="campaigns")
    approver = relationship("User", foreign_keys=[approved_by])
    budget_items = relationship("BudgetItem", back_populates="campaign", cascade="all, delete-orphan", order_by="BudgetItem.sort_order")
    milestones = relationship("Milestone", back_populates="campaign", cascade="all, delete-orphan", order_by="Milestone.sort_order")
    donations = relationship("Donation", back_populates="campaign", cascade="all, delete-orphan")
    feasibility_scores = relationship("FeasibilityScore", back_populates="campaign", cascade="all, delete-orphan")
    volunteer_opportunities = relationship("VolunteerOpportunity", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "category IN ('disaster_relief', 'education', 'healthcare', 'nutrition', 'environment', 'marathon_fundraiser', 'other')",
            name="chk_campaign_category"
        ),
        CheckConstraint(
            "status IN ('draft', 'pending_review', 'active', 'paused', 'completed', 'rejected', 'expired')",
            name="chk_campaign_status"
        ),
        CheckConstraint(
            "safety_tier IN ('open', 'trained_only', 'no_volunteers')",
            name="chk_campaign_safety_tier"
        ),
    )


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    unit = Column(String(50), nullable=True)
    unit_cost = Column(Numeric(10, 2), nullable=True)
    quantity = Column(Numeric(10, 2), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=False)
    benchmark_unit_cost = Column(Numeric(10, 2), nullable=True)
    benchmark_source = Column(String(255), nullable=True)
    benchmark_source_url = Column(Text, nullable=True)
    benchmark_resolution = Column(String(20), default="state", server_default=text("'state'"))  # 'district', 'state', 'national', 'custom'
    is_stale_adjusted = Column(Boolean, default=False, server_default=text("FALSE"))
    cost_ratio = Column(Numeric(5, 2), nullable=True)
    flag = Column(String(20), nullable=True)  # 'pass', 'warning', 'fail'
    sort_order = Column(Integer, default=0, server_default=text("0"))

    # Relationships
    campaign = relationship("Campaign", back_populates="budget_items")

    __table_args__ = (
        CheckConstraint("flag IS NULL OR flag IN ('pass', 'warning', 'fail')", name="chk_budget_item_flag"),
        CheckConstraint("benchmark_resolution IS NULL OR benchmark_resolution IN ('district', 'state', 'national', 'custom')", name="chk_budget_item_resolution"),
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)
    status = Column(String(20), default="pending", server_default=text("'pending'"), index=True)
    evidence_urls = Column(ARRAY(Text), nullable=True)
    evidence_hash = Column(String(64), nullable=True)
    blockchain_tx_hash = Column(String(66), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0, server_default=text("0"))

    # Relationships
    campaign = relationship("Campaign", back_populates="milestones")
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'evidence_submitted', 'verified', 'overdue', 'failed')",
            name="chk_milestone_status"
        ),
    )


class Donation(Base):
    __tablename__ = "donations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR", server_default=text("'INR'"))
    payment_method = Column(String(20), nullable=True)  # 'upi', 'card', 'netbanking', 'crypto'
    payment_gateway_order_id = Column(String(100), nullable=True)
    payment_gateway_payment_id = Column(String(100), nullable=True)
    status = Column(String(20), default="initiated", server_default=text("'initiated'"), index=True)
    blockchain_tx_hash = Column(String(66), nullable=True, index=True)
    blockchain_confirmed = Column(Boolean, default=False, server_default=text("FALSE"), index=True)
    donor_message = Column(Text, nullable=True)
    is_anonymous = Column(Boolean, default=False, server_default=text("FALSE"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    donor = relationship("User", back_populates="donations")
    campaign = relationship("Campaign", back_populates="donations")

    __table_args__ = (
        CheckConstraint(
            "status IN ('initiated', 'processing', 'completed', 'failed', 'refunded')",
            name="chk_donation_status"
        ),
        CheckConstraint(
            "payment_method IS NULL OR payment_method IN ('upi', 'card', 'netbanking', 'crypto')",
            name="chk_donation_payment_method"
        ),
    )


class TrustabilityScore(Base):
    __tablename__ = "trustability_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    ngo_id = Column(UUID(as_uuid=True), ForeignKey("ngo_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_legal_score = Column(Integer, nullable=True)
    financial_transparency_score = Column(Integer, nullable=True)
    operational_performance_score = Column(Integer, nullable=True)
    governance_score = Column(Integer, nullable=True)
    data_completeness_score = Column(Integer, nullable=True)
    overall_score = Column(Integer, nullable=True)
    overall_label = Column(String(20), nullable=True)
    methodology_version = Column(String(10), default="1.0", server_default=text("'1.0'"))
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"), index=True)
    breakdown = Column(JSONB, nullable=False)

    # Relationships
    ngo = relationship("NGOProfile", back_populates="trustability_scores")

    __table_args__ = (
        CheckConstraint(
            "overall_label IS NULL OR overall_label IN ('verified', 'partially_verified', 'unverified', 'insufficient_data', 'high_risk', 'under_review')",
            name="chk_trustability_overall_label"
        ),
    )


class FeasibilityScore(Base):
    __tablename__ = "feasibility_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    budget_realism_score = Column(Integer, nullable=True)
    cost_evidence_score = Column(Integer, nullable=True)
    beneficiary_consistency_score = Column(Integer, nullable=True)
    timeline_realism_score = Column(Integer, nullable=True)
    operational_capacity_score = Column(Integer, nullable=True)
    overall_score = Column(Integer, nullable=True)
    overall_label = Column(String(20), nullable=True)
    context_adjustments = Column(JSONB, nullable=True)
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"), index=True)
    breakdown = Column(JSONB, nullable=False)

    # Relationships
    campaign = relationship("Campaign", back_populates="feasibility_scores")

    __table_args__ = (
        CheckConstraint(
            "overall_label IS NULL OR overall_label IN ('high', 'moderate', 'needs_evidence', 'low', 'very_low', 'under_review')",
            name="chk_feasibility_overall_label"
        ),
    )


class CostBenchmark(Base):
    __tablename__ = "cost_benchmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    category = Column(String(100), nullable=False, index=True)
    item = Column(String(255), nullable=False, index=True)
    unit = Column(String(50), nullable=False)
    unit_cost_low = Column(Numeric(10, 2), nullable=True)
    unit_cost_mid = Column(Numeric(10, 2), nullable=True)
    unit_cost_high = Column(Numeric(10, 2), nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    country = Column(String(100), default="India", server_default=text("'India'"))
    source_name = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    authority_type = Column(String(50), default="statutory_order", server_default=text("'statutory_order'"))  # 'statutory_order', 'cpi_basket', 'market_survey', 'historical_average'
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    review_cycle_months = Column(Integer, default=12, server_default=text("12"))
    disaster_multiplier = Column(Numeric(3, 2), default=1.0, server_default=text("1.0"))
    rural_premium_pct = Column(Numeric(5, 2), default=0.0, server_default=text("0"))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_cost_benchmarks_location", "state", "district"),
        CheckConstraint(
            "authority_type IS NULL OR authority_type IN ('statutory_order', 'cpi_basket', 'market_survey', 'historical_average')",
            name="chk_cost_benchmark_authority_type"
        ),
    )


class VolunteerOpportunity(Base):
    __tablename__ = "volunteer_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    spots_total = Column(Integer, nullable=True)
    spots_filled = Column(Integer, default=0, server_default=text("0"))
    safety_tier = Column(String(20), default="open", server_default=text("'open'"), index=True)
    skills_required = Column(ARRAY(Text), nullable=True)
    min_age = Column(Integer, default=18, server_default=text("18"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    # Relationships
    campaign = relationship("Campaign", back_populates="volunteer_opportunities")
    applications = relationship("VolunteerApplication", back_populates="opportunity", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("safety_tier IN ('open', 'trained_only', 'no_volunteers')", name="chk_vol_opp_safety_tier"),
    )


class VolunteerApplication(Base):
    __tablename__ = "volunteer_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("volunteer_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="applied", server_default=text("'applied'"), index=True)
    applied_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    opportunity = relationship("VolunteerOpportunity", back_populates="applications")
    user = relationship("User", back_populates="volunteer_applications")
    credential = relationship("VolunteerCredential", back_populates="application", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('applied', 'approved', 'rejected', 'completed', 'no_show')",
            name="chk_vol_app_status"
        ),
    )


class VolunteerCredential(Base):
    __tablename__ = "volunteer_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    application_id = Column(UUID(as_uuid=True), ForeignKey("volunteer_applications.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    hours_logged = Column(Numeric(5, 1), nullable=True)
    ngo_confirmed = Column(Boolean, default=False, server_default=text("FALSE"))
    ngo_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    blockchain_tx_hash = Column(String(66), nullable=True, index=True)
    certificate_url = Column(Text, nullable=True)
    certificate_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    # Relationships
    application = relationship("VolunteerApplication", back_populates="credential")


class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    entity_type = Column(String(20), nullable=False)  # 'ngo', 'campaign'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    priority = Column(String(20), default="normal", server_default=text("'normal'"), index=True)
    flags = Column(JSONB, nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending", server_default=text("'pending'"), index=True)
    reviewer_notes = Column(Text, nullable=True)
    decision = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    reviewer = relationship("User", foreign_keys=[assigned_to])

    __table_args__ = (
        CheckConstraint("entity_type IN ('ngo', 'campaign')", name="chk_review_entity_type"),
        CheckConstraint("priority IN ('critical', 'high', 'normal', 'low')", name="chk_review_priority"),
        CheckConstraint("status IN ('pending', 'in_review', 'resolved', 'escalated')", name="chk_review_status"),
        CheckConstraint("decision IS NULL OR decision IN ('approved', 'rejected', 'needs_info', 'escalated')", name="chk_review_decision"),
        Index("idx_review_queue_entity", "entity_type", "entity_id"),
    )


class DonorReviewInvitation(Base):
    __tablename__ = "donor_review_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    donation_id = Column(UUID(as_uuid=True), ForeignKey("donations.id", ondelete="SET NULL"), nullable=True)
    magic_token = Column(String(64), unique=True, nullable=False, index=True)
    video_url = Column(Text, nullable=False)
    hearty_note_top = Column(Text, nullable=True)
    hearty_note_bottom = Column(Text, nullable=True)
    status = Column(String(20), default="pending", server_default=text("'pending'"), index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))
    voted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    milestone = relationship("Milestone")
    donor = relationship("User")
    donation = relationship("Donation")
    vote = relationship("DonorVote", back_populates="invitation", uselist=False, cascade="all, delete-orphan")


class DonorVote(Base):
    __tablename__ = "donor_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    invitation_id = Column(UUID(as_uuid=True), ForeignKey("donor_review_invitations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey("milestones.id", ondelete="CASCADE"), nullable=False, index=True)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vote = Column(String(20), nullable=False)  # 'thumbs_up', 'thumbs_down'
    feedback_note = Column(Text, nullable=True)
    blockchain_tx_hash = Column(String(66), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("NOW()"))

    # Relationships
    invitation = relationship("DonorReviewInvitation", back_populates="vote")
    milestone = relationship("Milestone")
    donor = relationship("User")

    __table_args__ = (
        CheckConstraint("vote IN ('thumbs_up', 'thumbs_down')", name="chk_donor_vote_type"),
    )

