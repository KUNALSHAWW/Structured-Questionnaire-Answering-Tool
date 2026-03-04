"""Generate sample PDF data for testing the questionnaire answering tool.

Creates:
  sample_data/questionnaire_vendor_assessment.pdf  — 10 vendor due-diligence questions
  sample_data/it_infrastructure_report.pdf         — Reference: IT systems & compliance
  sample_data/financial_summary.pdf                — Reference: Financials & audit info
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLE_DIR.mkdir(exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], spaceAfter=20)
heading_style = ParagraphStyle("CustomH2", parent=styles["Heading2"], spaceAfter=10)
body_style = ParagraphStyle("CustomBody", parent=styles["BodyText"], spaceAfter=8, leading=14)
q_style = ParagraphStyle("Question", parent=styles["BodyText"], spaceAfter=12, leading=15,
                          leftIndent=20, bulletIndent=10)

# ────────────────── Questionnaire PDF ──────────────────

def build_questionnaire():
    path = SAMPLE_DIR / "questionnaire_vendor_assessment.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    questions = [
        "What is NovaTech Solutions' primary business model and what are its main product lines?",
        "Describe the company's IT infrastructure including data center locations, cloud providers, and disaster recovery capabilities.",
        "What cybersecurity certifications does NovaTech currently hold, and when were they last audited?",
        "What is the company's annual revenue and what has been the year-over-year revenue growth rate for the past three years?",
        "Describe the company's data backup strategy, including backup frequency, retention periods, and recovery time objectives.",
        "How many employees does NovaTech have, and what is the current employee turnover rate?",
        "What is NovaTech's approach to environmental sustainability and what are its carbon reduction targets?",
        "Does the company have a formal vendor risk management program? If so, describe the key components.",
        "What financial auditing standards does NovaTech follow, and who is the external auditor?",
        "Describe the company's business continuity plan, including how often it is tested and the results of the most recent test.",
    ]

    story = [
        Paragraph("NovaTech Solutions — Vendor Due-Diligence Questionnaire", title_style),
        Paragraph("This questionnaire must be completed as part of the vendor assessment process. "
                   "Please provide detailed responses referencing supporting documentation where applicable.", body_style),
        Spacer(1, 16),
    ]
    for i, q in enumerate(questions, 1):
        story.append(Paragraph(f"<b>Q{i}.</b> {q}", q_style))

    doc.build(story)
    print(f"  ✓ {path.name}")


# ────────────────── IT Infrastructure Reference PDF ──────────────────

def build_it_infrastructure():
    path = SAMPLE_DIR / "it_infrastructure_report.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    story = [
        Paragraph("NovaTech Solutions — IT Infrastructure & Security Report", title_style),
        Paragraph("Prepared by: IT Governance Office | Classification: Confidential | Date: January 2026", body_style),
        Spacer(1, 12),

        Paragraph("1. Infrastructure Overview", heading_style),
        Paragraph(
            "NovaTech Solutions operates a hybrid cloud infrastructure combining on-premises data centers "
            "with Amazon Web Services (AWS) and Microsoft Azure cloud deployments. The primary data center "
            "is located in Austin, Texas, with a secondary disaster recovery site in Portland, Oregon. "
            "Both facilities are Tier III certified and provide N+1 redundancy for power and cooling systems. "
            "The company migrated 72% of production workloads to AWS us-east-1 in Q3 2025, retaining "
            "legacy ERP and financial systems on-premises.", body_style),
        Spacer(1, 8),

        Paragraph("2. Cybersecurity Certifications & Compliance", heading_style),
        Paragraph(
            "NovaTech holds the following active certifications: ISO 27001:2022 (recertified October 2025), "
            "SOC 2 Type II (audit completed August 2025 by Deloitte), and PCI DSS Level 2 (validated March 2025). "
            "The company undergoes annual penetration testing performed by CrowdStrike, with the most recent "
            "engagement completed in November 2025 identifying zero critical vulnerabilities and three medium-risk "
            "findings, all remediated within 30 days. The information security team consists of 14 full-time "
            "staff led by CISO Margaret Chen.", body_style),
        Spacer(1, 8),

        Paragraph("3. Data Backup & Recovery", heading_style),
        Paragraph(
            "Production databases are backed up every 4 hours using AWS Backup with cross-region replication "
            "to us-west-2. Full system snapshots are taken daily at 02:00 UTC and retained for 90 days. "
            "Archive backups are stored in AWS S3 Glacier with a 7-year retention policy to comply with "
            "regulatory requirements. The Recovery Time Objective (RTO) is 4 hours for critical systems "
            "and 24 hours for non-critical workloads. The Recovery Point Objective (RPO) is 1 hour for "
            "transactional databases and 4 hours for document storage.", body_style),
        Spacer(1, 8),

        Paragraph("4. Disaster Recovery & Business Continuity", heading_style),
        Paragraph(
            "NovaTech's Business Continuity Plan (BCP) was last updated in September 2025 and is reviewed "
            "quarterly by the Risk Committee. DR failover tests are conducted bi-annually, with the most "
            "recent full-scale test on December 5, 2025, achieving successful failover of all critical "
            "applications to the Portland DR site within 3.5 hours (within the 4-hour RTO target). "
            "Communication during incidents follows a defined escalation matrix with automated alerts "
            "via PagerDuty and Slack integration.", body_style),
        Spacer(1, 8),

        Paragraph("5. Vendor Risk Management", heading_style),
        Paragraph(
            "NovaTech maintains a formal Vendor Risk Management (VRM) program governed by the Procurement "
            "& Risk team. All vendors handling customer data undergo an annual security questionnaire, "
            "evidence collection, and risk scoring process. Tier 1 vendors (those with access to PII or "
            "critical infrastructure) are subject to on-site audits every 18 months. The current vendor "
            "register contains 847 active vendors, of which 63 are classified as Tier 1. The VRM program "
            "was externally benchmarked against the Shared Assessments SIG framework in 2025.", body_style),
        Spacer(1, 8),

        Paragraph("6. Network Architecture", heading_style),
        Paragraph(
            "The corporate network uses a zero-trust architecture implemented via Zscaler Private Access "
            "for remote employees and Palo Alto Networks firewalls for on-premises perimeter security. "
            "All inter-site traffic is encrypted using IPsec VPN tunnels with AES-256 encryption. "
            "Endpoint detection and response (EDR) is provided by CrowdStrike Falcon deployed on "
            "100% of managed endpoints (2,847 devices as of January 2026). Multi-factor authentication "
            "is mandatory for all employee accounts, with YubiKey hardware tokens issued to privileged users.", body_style),
    ]

    doc.build(story)
    print(f"  ✓ {path.name}")


# ────────────────── Financial Summary Reference PDF ──────────────────

def build_financial_summary():
    path = SAMPLE_DIR / "financial_summary.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    story = [
        Paragraph("NovaTech Solutions — Financial Summary & Audit Report", title_style),
        Paragraph("Fiscal Year 2025 | Prepared by: Finance Department | Auditor: KPMG LLP", body_style),
        Spacer(1, 12),

        Paragraph("1. Revenue & Growth", heading_style),
        Paragraph(
            "NovaTech Solutions reported total revenue of $78.4 million for fiscal year 2025, representing "
            "a 15.2% increase from $68.1 million in FY2024. FY2023 revenue was $59.3 million, giving a "
            "three-year compound annual growth rate (CAGR) of 14.9%. The SaaS product line contributed "
            "$52.1 million (66.5% of total revenue), while professional services accounted for $18.7 million "
            "(23.8%) and licensing revenue was $7.6 million (9.7%). Annual Recurring Revenue (ARR) reached "
            "$48.3 million, up 22% year-over-year, with a net revenue retention rate of 118%.", body_style),
        Spacer(1, 8),

        Paragraph("2. Profitability", heading_style),
        Paragraph(
            "Gross profit margin was 71.3% in FY2025, up from 68.9% in FY2024, driven by increased SaaS "
            "mix and infrastructure cost optimization. Operating income was $11.8 million (15.1% operating "
            "margin), compared to $8.2 million (12.0%) in the prior year. EBITDA was $15.4 million with an "
            "EBITDA margin of 19.6%. Net income after tax was $9.1 million. The company maintains a strong "
            "balance sheet with $23.7 million in cash and short-term investments and zero long-term debt.", body_style),
        Spacer(1, 8),

        Paragraph("3. External Audit", heading_style),
        Paragraph(
            "The FY2025 financial statements were audited by KPMG LLP in accordance with U.S. Generally "
            "Accepted Accounting Principles (GAAP) and International Financial Reporting Standards (IFRS). "
            "KPMG issued an unqualified (clean) opinion dated February 15, 2026, with no material weaknesses "
            "identified in internal controls over financial reporting. The audit committee meeting held on "
            "February 20, 2026, accepted the audit findings. NovaTech has used KPMG as its external auditor "
            "since 2019, with mandatory partner rotation occurring in 2024.", body_style),
        Spacer(1, 8),

        Paragraph("4. Workforce & HR Metrics", heading_style),
        Paragraph(
            "As of December 31, 2025, NovaTech employs 342 full-time equivalent (FTE) employees across "
            "four offices. Engineering accounts for 156 staff (45.6%), sales and marketing 87 (25.4%), "
            "customer success 54 (15.8%), and G&A functions 45 (13.2%). The annual voluntary turnover rate "
            "was 11.2% in FY2025, down from 13.8% in FY2024. The company offers a hybrid work model with "
            "employees required to be in-office two days per week. Average employee tenure is 3.4 years, "
            "and the company invested $1.2 million in employee training and development programs.", body_style),
        Spacer(1, 8),

        Paragraph("5. Environmental, Social & Governance (ESG)", heading_style),
        Paragraph(
            "NovaTech published its first standalone ESG report in 2025, aligned with the Global Reporting "
            "Initiative (GRI) Standards. The company has committed to achieving carbon neutrality for Scope 1 "
            "and Scope 2 emissions by 2028 and a 50% reduction in Scope 3 emissions by 2030. In FY2025, "
            "total Scope 1+2 emissions were 1,247 metric tons of CO2e, down 18% from the prior year. "
            "The Austin data center transitioned to 100% renewable energy in Q2 2025 through a power "
            "purchase agreement with a local wind farm. The board of directors includes 40% female "
            "representation and 30% underrepresented minority representation, exceeding NASDAQ diversity "
            "listing requirements.", body_style),
    ]

    doc.build(story)
    print(f"  ✓ {path.name}")


if __name__ == "__main__":
    print("Generating sample PDF files...")
    build_questionnaire()
    build_it_infrastructure()
    build_financial_summary()
    print(f"\nAll PDFs saved to: {SAMPLE_DIR}")
