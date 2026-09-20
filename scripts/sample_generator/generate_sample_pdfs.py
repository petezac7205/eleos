"""
Sample PDF Package Generator for ELEOS Scenarios.
Uses ReportLab to generate multi-page, realistic Indian non-profit document packages:
1. NGO_Clean.pdf (High Trust: Valid Deed, Form 10AC, Clean Audit with UDIN, Corroborated Projects)
2. NGO_HighAdmin.pdf (Overhead Anomaly: Admin Ratio 48%, Expired 80G, Outlier flag)
3. NGO_Anomaly_Case.pdf (Accounting Discrepancy & Uncorroborated Projects: ₹15L mismatch, uncorroborated claims)
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "sample_docs"
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)


def build_clean_ngo_pdf(target_path: Path):
    doc = SimpleDocTemplate(str(target_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#1e293b"))
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#64748b"))
    section_style = ParagraphStyle('SectionH', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor("#0f766e"), spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#334155"))
    meta_style = ParagraphStyle('MetaTable', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#1e293b"))

    # PAGE 1: TRUST DEED / REGISTRATION CERTIFICATE
    story.append(Paragraph("GOVERNMENT OF TAMIL NADU - REGISTRATION DEPARTMENT", subtitle_style))
    story.append(Paragraph("CERTIFICATE OF REGISTRATION UNDER INDIAN TRUSTS ACT, 1882", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("This is to certify that <b>HopeRelief Foundation</b> having its registered office at No. 14, Gandhi Road, Chennai, Tamil Nadu - 600001 has been duly registered as a Public Charitable Trust.", body_style))
    story.append(Spacer(1, 8))

    deed_data = [
        [Paragraph("<b>Registration Number:</b>", meta_style), Paragraph("TR/2019/CHN/1029", meta_style), Paragraph("<b>Date of Registration:</b>", meta_style), Paragraph("2019-04-12", meta_style)],
        [Paragraph("<b>Registration Authority:</b>", meta_style), Paragraph("Sub-Registrar Office, Chennai Central", meta_style), Paragraph("<b>Legal Entity Type:</b>", meta_style), Paragraph("Trust", meta_style)],
        [Paragraph("<b>PAN Number:</b>", meta_style), Paragraph("AAATH1234F", meta_style), Paragraph("<b>State / District:</b>", meta_style), Paragraph("Tamil Nadu / Chennai", meta_style)],
        [Paragraph("<b>Governing Act:</b>", meta_style), Paragraph("Indian Trusts Act, 1882", meta_style), Paragraph("<b>FCRA Status:</b>", meta_style), Paragraph("Valid (Reg No: 076210234)", meta_style)],
    ]
    t1 = Table(deed_data, colWidths=[120, 150, 120, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # PAGE 1 PART 2: FORM 10AC TAX EXEMPTION ORDER (12A & 80G)
    story.append(Paragraph("INCOME TAX DEPARTMENT (CENTRAL BOARD OF DIRECT TAXES)", subtitle_style))
    story.append(Paragraph("FORM 10AC - ORDER FOR REGISTRATION UNDER SECTION 12A & SECTION 80G", section_style))
    story.append(Paragraph("Order issued under clause (i) of sub-section (1) of Section 12AB and clause (i) of first proviso to sub-section (5) of Section 80G of the Income-tax Act, 1961.", body_style))
    story.append(Spacer(1, 6))

    tax_data = [
        [Paragraph("<b>Section 12A URN:</b>", meta_style), Paragraph("AAATH1234FE20214", meta_style), Paragraph("<b>12A Valid Until:</b>", meta_style), Paragraph("2026-05-14", meta_style)],
        [Paragraph("<b>Section 80G URN:</b>", meta_style), Paragraph("AAATH1234FD20218", meta_style), Paragraph("<b>80G Valid Until:</b>", meta_style), Paragraph("2026-05-14", meta_style)],
        [Paragraph("<b>Tax Assessment Year:</b>", meta_style), Paragraph("2021-22 to 2026-27", meta_style), Paragraph("<b>Status:</b>", meta_style), Paragraph("Approved / Active", meta_style)]
    ]
    t2 = Table(tax_data, colWidths=[120, 150, 120, 150])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#86efac")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#bbf7d0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t2)
    story.append(PageBreak())

    # PAGE 2: AUDITED BALANCE SHEET & INCOME & EXPENDITURE ACCOUNT (FY2024-25)
    story.append(Paragraph("R. K. SWAMY & ASSOCIATES — CHARTERED ACCOUNTANTS", subtitle_style))
    story.append(Paragraph("INDEPENDENT AUDITOR'S REPORT & AUDITED FINANCIAL STATEMENTS", title_style))
    story.append(Paragraph("<b>Entity:</b> HopeRelief Foundation | <b>PAN:</b> AAATH1234F | <b>Financial Year:</b> FY2024-25", subtitle_style))
    story.append(Paragraph("<b>Auditor Opinion:</b> Unqualified (Clean) Opinion. In our opinion, the financial statements give a true and fair view of the state of affairs of the Trust in conformity with accounting principles generally accepted in India.", body_style))
    story.append(Paragraph("<b>Auditor Details:</b> CA R. K. Swamy (M.No: 045129) | Firm Reg No: 004128S | <b>ICAI UDIN:</b> 25045129BCAE198234", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>INCOME & EXPENDITURE ACCOUNT FOR THE YEAR ENDED 31ST MARCH 2025</b>", section_style))
    fin_data = [
        [Paragraph("<b>Particulars</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style), Paragraph("<b>Particulars</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style)],
        [Paragraph("To Programme Expenses (Relief & Education)", meta_style), Paragraph("1,90,00,000.00", meta_style), Paragraph("By Institutional Grant Receipts", meta_style), Paragraph("1,85,00,000.00", meta_style)],
        [Paragraph("To Administrative & Office Overheads", meta_style), Paragraph("20,90,000.00", meta_style), Paragraph("By Individual Voluntary Donations", meta_style), Paragraph("42,50,000.00", meta_style)],
        [Paragraph("To Employee Benefit Expenses", meta_style), Paragraph("11,60,000.00", meta_style), Paragraph("By Bank Interest & Other Incomes", meta_style), Paragraph("4,50,000.00", meta_style)],
        [Paragraph("To Fundraising & Public Outreach", meta_style), Paragraph("4,60,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("To Material & Supply Distributions", meta_style), Paragraph("2,30,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("To Consultancy & Professional Fees", meta_style), Paragraph("1,15,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("To Other Residual Expenses", meta_style), Paragraph("1,45,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("<b>TOTAL EXPENDITURE (A)</b>", meta_style), Paragraph("<b>2,32,00,000.00</b>", meta_style), Paragraph("<b>TOTAL INCOME (B)</b>", meta_style), Paragraph("<b>2,32,00,000.00</b>", meta_style)],
        [Paragraph("<b>Net Operating Surplus (B - A)</b>", meta_style), Paragraph("<b>0.00</b>", meta_style), Paragraph("<b>Cash & Bank Balance (As on 31 Mar)</b>", meta_style), Paragraph("<b>48,50,000.00</b>", meta_style)],
        [Paragraph("<b>Total Assets</b>", meta_style), Paragraph("<b>2,55,00,000.00</b>", meta_style), Paragraph("<b>Total Liabilities</b>", meta_style), Paragraph("<b>35,00,000.00</b>", meta_style)]
    ]
    t3 = Table(fin_data, colWidths=[180, 90, 180, 90])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t3)
    story.append(PageBreak())

    # PAGE 3: ANNUAL PROJECT SUMMARY & CORROBORATING EVIDENCE
    story.append(Paragraph("HOPERELIEF FOUNDATION - ANNUAL OPERATIONS & PROJECT REPORT", title_style))
    story.append(Paragraph("<b>Reporting Period:</b> FY 2024-25 | <b>Primary Focus:</b> Disaster Relief & Livelihoods", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Summary of Programmatic Projects Executed:</b>", section_style))

    prj_data = [
        [Paragraph("<b>Project Title</b>", meta_style), Paragraph("<b>Funder / Partner</b>", meta_style), Paragraph("<b>Cost (INR)</b>", meta_style), Paragraph("<b>Beneficiaries</b>", meta_style), Paragraph("<b>Status</b>", meta_style)],
        [Paragraph("South Asia Flood Relief Mission", meta_style), Paragraph("UNICEF / Disaster Aid Consortium", meta_style), Paragraph("1,10,00,000.00", meta_style), Paragraph("45,000", meta_style), Paragraph("Completed", meta_style)],
        [Paragraph("Rural School Hygiene & Sanitization", meta_style), Paragraph("Tamil Nadu State Education Dept", meta_style), Paragraph("50,00,000.00", meta_style), Paragraph("12,000", meta_style), Paragraph("Completed", meta_style)],
        [Paragraph("Emergency Shelter Deployment", meta_style), Paragraph("NDRF Partner Grant", meta_style), Paragraph("25,00,000.00", meta_style), Paragraph("8,500", meta_style), Paragraph("Completed", meta_style)],
        [Paragraph("<b>Total Programmatic Project Outlay:</b>", meta_style), Paragraph("<b>3 Verified Institutional Funders</b>", meta_style), Paragraph("<b>1,85,00,000.00</b>", meta_style), Paragraph("<b>65,500</b>", meta_style), Paragraph("<b>100% Executed</b>", meta_style)]
    ]
    t4 = Table(prj_data, colWidths=[150, 140, 90, 80, 80])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t4)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Independent Corroboration Note:</b> All three projects operate with formal institutional grant sanctions matching the ₹1.85 Cr grant income reflected on the statutory audited financial statements. Average programme cost per beneficiary is ₹282.44, well within regional disaster relief benchmarks.", body_style))

    doc.build(story)


def build_high_admin_ngo_pdf(target_path: Path):
    """Generates an NGO with high administrative overhead (48%) and expired 80G."""
    doc = SimpleDocTemplate(str(target_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#1e293b"))
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#64748b"))
    section_style = ParagraphStyle('SectionH', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor("#b45309"), spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#334155"))
    meta_style = ParagraphStyle('MetaTable', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#1e293b"))

    story.append(Paragraph("GOVERNMENT OF MAHARASHTRA — REGISTRAR OF SOCIETIES", subtitle_style))
    story.append(Paragraph("CERTIFICATE OF REGISTRATION UNDER SOCIETIES ACT, 1860", title_style))
    story.append(Paragraph("This is to certify that <b>Teach For Change India</b> having office at Nariman Point, Mumbai is registered as a Charitable Society.", body_style))
    story.append(Spacer(1, 8))

    deed_data = [
        [Paragraph("<b>Registration Number:</b>", meta_style), Paragraph("U85300MH2020NPL12984", meta_style), Paragraph("<b>Date of Registration:</b>", meta_style), Paragraph("2020-02-18", meta_style)],
        [Paragraph("<b>Registration Authority:</b>", meta_style), Paragraph("Registrar of Societies, Mumbai", meta_style), Paragraph("<b>Legal Entity Type:</b>", meta_style), Paragraph("Society", meta_style)],
        [Paragraph("<b>PAN Number:</b>", meta_style), Paragraph("AAACT9012M", meta_style), Paragraph("<b>State / District:</b>", meta_style), Paragraph("Maharashtra / Mumbai", meta_style)],
        [Paragraph("<b>Section 12A URN:</b>", meta_style), Paragraph("AAACT9012ME20221 (Valid)", meta_style), Paragraph("<b>Section 80G URN:</b>", meta_style), Paragraph("AAACT9012MD20225 (Expired 2024)", meta_style)],
    ]
    t1 = Table(deed_data, colWidths=[120, 150, 120, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fffbeb")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fde68a")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fef3c7")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # AUDITED STATEMENT - 48% ADMIN OVERHEAD
    story.append(Paragraph("AUDITED INCOME & EXPENDITURE STATEMENT (FY2024-25)", section_style))
    story.append(Paragraph("<b>Auditor:</b> K. S. Mehta & Co. (M.No: 021489) | <b>UDIN:</b> 25021489ABCD987123 | <b>Opinion:</b> Qualified", body_style))
    story.append(Paragraph("<i>Auditor Note: The Society's administrative disbursements represent 48.0% of total expenditure. High executive salaries and marketing overheads noted.</i>", body_style))
    story.append(Spacer(1, 6))

    fin_data = [
        [Paragraph("<b>Expenditure Item</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style), Paragraph("<b>Income Item</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style)],
        [Paragraph("Direct Educational Programme Expenses", meta_style), Paragraph("44,00,000.00", meta_style), Paragraph("Public Donations & CSR Receipts", meta_style), Paragraph("1,00,00,000.00", meta_style)],
        [Paragraph("Administrative & Executive Compensation", meta_style), Paragraph("48,00,000.00", meta_style), Paragraph("Interest Income", meta_style), Paragraph("2,00,000.00", meta_style)],
        [Paragraph("Fundraising & Public Events", meta_style), Paragraph("5,00,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("Other Operating Expenses", meta_style), Paragraph("3,00,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("<b>TOTAL EXPENDITURE (A)</b>", meta_style), Paragraph("<b>1,00,00,000.00</b>", meta_style), Paragraph("<b>TOTAL INCOME (B)</b>", meta_style), Paragraph("<b>1,02,00,000.00</b>", meta_style)],
        [Paragraph("<b>Net Surplus (B - A)</b>", meta_style), Paragraph("<b>2,00,00,00.00</b>", meta_style), Paragraph("<b>Admin Ratio %</b>", meta_style), Paragraph("<b>48.0%</b>", meta_style)]
    ]
    t2 = Table(fin_data, colWidths=[180, 90, 180, 90])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fde68a")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t2)
    doc.build(story)


def build_fraudulent_ngo_pdf(target_path: Path):
    """Generates an NGO with a ₹15 Lakh arithmetic mismatch and uncorroborated project claims."""
    doc = SimpleDocTemplate(str(target_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#991b1b"))
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, leading=14, alignment=1, textColor=colors.HexColor("#64748b"))
    section_style = ParagraphStyle('SectionH', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor("#991b1b"), spaceAfter=6)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#334155"))
    meta_style = ParagraphStyle('MetaTable', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor("#1e293b"))

    story.append(Paragraph("GOVERNMENT OF KARNATAKA — SUB-REGISTRAR OFFICE", subtitle_style))
    story.append(Paragraph("CERTIFICATE OF REGISTRATION — TRUST DEED", title_style))
    story.append(Paragraph("This is to certify that <b>Pragati Rural Development Trust</b> is registered at Bengaluru, Karnataka.", body_style))
    story.append(Spacer(1, 8))

    deed_data = [
        [Paragraph("<b>Registration Number:</b>", meta_style), Paragraph("TR/2021/BLR/4421", meta_style), Paragraph("<b>Date of Registration:</b>", meta_style), Paragraph("2021-08-10", meta_style)],
        [Paragraph("<b>Registration Authority:</b>", meta_style), Paragraph("Sub-Registrar Bengaluru South", meta_style), Paragraph("<b>Legal Entity Type:</b>", meta_style), Paragraph("Trust", meta_style)],
        [Paragraph("<b>PAN Number:</b>", meta_style), Paragraph("AAATP9876K", meta_style), Paragraph("<b>State / District:</b>", meta_style), Paragraph("Karnataka / Bengaluru", meta_style)],
        [Paragraph("<b>Section 12A URN:</b>", meta_style), Paragraph("Not Documented / Missing", meta_style), Paragraph("<b>Section 80G URN:</b>", meta_style), Paragraph("Not Documented / Missing", meta_style)],
    ]
    t1 = Table(deed_data, colWidths=[120, 150, 120, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fca5a5")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fee2e2")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # AUDITED STATEMENT WITH DELIBERATE ARITHMETIC MISMATCH (15 Lakhs difference)
    story.append(Paragraph("AUDITED INCOME & EXPENDITURE ACCOUNT (FY2024-25)", section_style))
    story.append(Paragraph("<b>Auditor:</b> Verma & Co. | <b>UDIN:</b> Missing / Not Stated | <b>Opinion:</b> Adverse", body_style))
    story.append(Spacer(1, 6))

    fin_data = [
        [Paragraph("<b>Particulars</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style), Paragraph("<b>Particulars</b>", meta_style), Paragraph("<b>Amount (INR)</b>", meta_style)],
        [Paragraph("Programme Distributions", meta_style), Paragraph("30,00,000.00", meta_style), Paragraph("Voluntary Public Donations", meta_style), Paragraph("65,00,000.00", meta_style)],
        [Paragraph("Administrative Overhead", meta_style), Paragraph("10,00,000.00", meta_style), Paragraph("Institutional Grants (Audited)", meta_style), Paragraph("0.00", meta_style)],
        [Paragraph("Employee Salaries", meta_style), Paragraph("5,00,000.00", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("<b>Sum of Itemized Categories</b>", meta_style), Paragraph("<b>45,00,000.00</b>", meta_style), Paragraph("", meta_style), Paragraph("", meta_style)],
        [Paragraph("<b>Reported Total Expenditure</b>", meta_style), Paragraph("<b>60,00,000.00</b>", meta_style), Paragraph("<b>TOTAL INCOME</b>", meta_style), Paragraph("<b>65,00,000.00</b>", meta_style)],
        [Paragraph("<b>Unreconciled Variance</b>", meta_style), Paragraph("<b>15,00,000.00 (25.0%)</b>", meta_style), Paragraph("<b>Audit Status</b>", meta_style), Paragraph("<b>Adverse Discrepancy</b>", meta_style)]
    ]
    t2 = Table(fin_data, colWidths=[180, 90, 180, 90])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fee2e2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#ef4444")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#fca5a5")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # UNCORROBORATED PROJECT CLAIM
    story.append(Paragraph("<b>OPERATIONAL PROJECT CLAIMS (SELF-REPORTED ACTIVITY)</b>", section_style))
    story.append(Paragraph("The Trust claims execution of <i>Project Gramin Suraksha</i> totaling <b>INR 80,00,000.00</b> purportedly funded by UNICEF. However, the statutory Income & Expenditure statement reveals exactly <b>INR 0.00</b> in audited institutional grants, demonstrating an uncorroborated operational claim.", body_style))
    doc.build(story)


def generate_all_sample_pdfs():
    clean_pdf = SAMPLE_DOCS_DIR / "NGO_Clean.pdf"
    high_admin_pdf = SAMPLE_DOCS_DIR / "NGO_HighAdmin.pdf"
    fraud_pdf = SAMPLE_DOCS_DIR / "NGO_Anomaly_Case.pdf"

    print("Generating sample PDF packages in data/sample_docs/...")
    build_clean_ngo_pdf(clean_pdf)
    print(f"  [SUCCESS] Created {clean_pdf}")
    build_high_admin_ngo_pdf(high_admin_pdf)
    print(f"  [SUCCESS] Created {high_admin_pdf}")
    build_fraudulent_ngo_pdf(fraud_pdf)
    print(f"  [SUCCESS] Created {fraud_pdf}")


if __name__ == "__main__":
    generate_all_sample_pdfs()

