"""
Canonical Pydantic Schema for Extracted NGO Document Packages.
Both Pipeline A (Gemini VLM) and Pipeline B (AWS Textract + Bedrock) must emit this schema.
"""

from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """Represents a single extracted data point with traceability to source document."""
    value: Optional[Union[str, float, int, bool]] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_document: str = "Unknown"
    page_number: Optional[int] = None


class CanonicalIdentity(BaseModel):
    """Identity & Legal Registration fields."""
    ngo_name: ExtractedField
    registration_type: ExtractedField  # "Trust" | "Society" | "Section 8"
    registration_number: ExtractedField
    registration_authority: ExtractedField
    act_name: ExtractedField
    date_of_registration: ExtractedField  # "YYYY-MM-DD"
    pan: ExtractedField
    state: ExtractedField
    district: ExtractedField


class CanonicalTaxCompliance(BaseModel):
    """Statutory tax exemptions and foreign contribution compliance."""
    has_12a: ExtractedField
    urn_12a: Optional[ExtractedField] = None
    valid_until_12a: Optional[ExtractedField] = None
    has_80g: ExtractedField
    urn_80g: Optional[ExtractedField] = None
    valid_until_80g: Optional[ExtractedField] = None
    fcra_status: ExtractedField  # "Valid" | "Expired" | "Not Applicable"
    fcra_number: Optional[ExtractedField] = None


class CanonicalAnnualFinancial(BaseModel):
    """Financial figures extracted from audited financial statements."""
    financial_year: ExtractedField  # e.g. "FY2024-25"
    audit_opinion: ExtractedField  # "Clean" | "Qualified" | "Adverse" | "Disclaimer"
    auditor_name: Optional[ExtractedField] = None
    ca_firm_registration_no: Optional[ExtractedField] = None
    udin: Optional[ExtractedField] = None  # ICAI 18-digit Unique Document Identification Number
    total_income: ExtractedField
    grant_income: Optional[ExtractedField] = None
    donation_income: Optional[ExtractedField] = None
    total_expenditure: ExtractedField
    programme_expenses: ExtractedField
    administrative_expenses: ExtractedField
    fundraising_expenses: Optional[ExtractedField] = None
    employee_expenses: Optional[ExtractedField] = None
    cash_and_bank_balance: Optional[ExtractedField] = None
    total_assets: Optional[ExtractedField] = None
    total_liabilities: Optional[ExtractedField] = None


class CanonicalProject(BaseModel):
    """Operational project details extracted from annual reports or project briefs."""
    project_name: ExtractedField
    status: ExtractedField  # "Completed" | "Ongoing" | "Planned"
    funder_name: Optional[ExtractedField] = None
    beneficiaries_reported: Optional[ExtractedField] = None
    reported_cost: Optional[ExtractedField] = None
    location_state: Optional[ExtractedField] = None
    location_district: Optional[ExtractedField] = None
    outcomes_reported: Optional[ExtractedField] = None


class CanonicalNgoDocumentBundle(BaseModel):
    """Consolidated document bundle representing all extracted data from an NGO's uploaded packet."""
    extraction_provider: Literal["gemini", "aws_textract_bedrock", "synthetic_mock"] = "synthetic_mock"
    extraction_provider: Literal["gemini", "aws_textract_bedrock", "standard_reference"] = "standard_reference"
    identity: CanonicalIdentity
    compliance: CanonicalTaxCompliance
    financials: List[CanonicalAnnualFinancial] = Field(default_factory=list)
    projects: List[CanonicalProject] = Field(default_factory=list)
    raw_document_hashes: Dict[str, str] = Field(default_factory=dict)  # filename -> sha256_hash

