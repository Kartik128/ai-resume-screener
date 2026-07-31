#!/usr/bin/env python3
"""
=============================================================================
AI Resume Screener — End-to-End Test Runner
2 Complex JDs  ×  10 Diverse Resumes  →  Ranked Leaderboard
=============================================================================
"""

import asyncio
import json
import sys
import time
import io
import httpx
from typing import Optional

BASE_URL = "http://127.0.0.1:8099/api/v1"
LOGIN_EMAIL = "admin@company.com"
LOGIN_PASS = "admin"

# ─────────────────────────────────────────────────────────────────────────────
# JD 1: Senior Product Manager — FinTech / Payments (cross-functional, non-pure-tech)
# ─────────────────────────────────────────────────────────────────────────────
JD_1 = """
Senior Product Manager – Payments & FinTech Platform

Company: NovaPay Technologies | Location: San Francisco, CA (Hybrid, 3 days/week in office)
Salary Range: $160,000 – $210,000 + Equity + Bonus | Department: Product Management

About the Role:
NovaPay Technologies is a Series C FinTech company processing $4B+ in annual payment volume.
We're seeking a Senior Product Manager to own our core Payments Platform, driving strategy,
roadmap, and execution for payment processing, fraud prevention, and merchant integrations.

Required Qualifications (Must Have):
- 6–10 years of total Product Management experience, with at least 3 years in Payments, FinTech, or Banking
- Deep understanding of payment rails: ACH, card networks (Visa/Mastercard), real-time payments (RTP, FedNow)
- Proven experience with payment APIs and REST API design (working with engineering on API products)
- Experience with fraud detection and risk management frameworks in a payments context
- Strong data analysis skills: SQL, Tableau, Amplitude, Mixpanel, or equivalent analytics tools
- Track record of owning 0-to-1 products and scaling from MVP to $100M+ GMV
- Experience writing detailed PRDs (Product Requirements Documents) and working in Agile/Scrum teams
- Outstanding stakeholder management — ability to align cross-functional teams (Engineering, Design, Legal, Compliance, Finance)
- Familiarity with PCI-DSS compliance, AML/KYC regulations, and financial services regulatory framework
- Bachelor's degree in Business, Computer Science, Economics, or related field

Nice to Have:
- MBA from a top-tier university
- Previous experience at a Payments company (Stripe, Braintree, Adyen, Square, PayPal, Checkout.com)
- Experience with BNPL (Buy Now Pay Later) or embedded finance products
- Familiarity with ISO 20022 payment messaging standards
- Prior experience as a software engineer or strong technical background
- Experience launching products internationally (multi-currency, cross-border payments)

Key Responsibilities:
- Define and own the 12-month product roadmap for the NovaPay core payments platform
- Write detailed PRDs, user stories, and acceptance criteria for engineering teams
- Partner with design, engineering, data, compliance, and legal to ship high-quality products
- Drive merchant onboarding improvements reducing time-to-first-transaction from 5 days to 24 hours
- Analyze payment funnel conversion metrics and identify optimization opportunities
- Lead quarterly OKR planning and present product strategy to executive leadership
- Manage external partnerships with card networks, banking partners, and payment processors
"""

# ─────────────────────────────────────────────────────────────────────────────
# JD 2: Principal Data Engineer — Healthcare / Clinical Analytics (enterprise data)
# ─────────────────────────────────────────────────────────────────────────────
JD_2 = """
Principal Data Engineer – Clinical Analytics & Healthcare Data Platform

Company: HealthAI Systems | Location: Austin, TX (Remote-first, quarterly onsite)
Salary Range: $170,000 – $220,000 + Stock Options | Department: Data Engineering

About the Role:
HealthAI Systems builds AI-powered clinical intelligence tools used by 400+ hospital networks.
We're seeking a Principal Data Engineer to architect and lead development of our HIPAA-compliant
healthcare data platform, ingesting clinical, billing, and genomics data at petabyte scale.

Required Qualifications (Must Have):
- 8+ years of data engineering experience, with 3+ years in healthcare, clinical, or life sciences
- Expert proficiency in Python (data pipelines, ETL automation, PySpark transformations)
- Apache Spark / PySpark at scale — experience processing 50TB+ healthcare datasets
- Cloud data platform expertise: AWS (S3, Glue, Redshift, EMR) OR Google Cloud (BigQuery, Dataflow, GCS)
- Strong SQL / PostgreSQL for complex analytical queries and data modeling
- Deep expertise in healthcare data standards: HL7 v2, FHIR R4, ICD-10, CPT codes, LOINC
- HIPAA compliance and PHI data security: encryption at rest/transit, audit logging, data masking
- Data pipeline orchestration: Apache Airflow or Prefect or Dagster
- Experience with data lake architecture (Delta Lake, Apache Iceberg, or Apache Hudi)
- dbt (data build tool) for data transformation and documentation
- Proficiency with streaming data: Apache Kafka or AWS Kinesis for real-time clinical event processing
- Experience leading a team of 3–5 data engineers (technical mentorship and code reviews)

Nice to Have:
- Experience with HL7 FHIR APIs (SMART on FHIR, CDS Hooks)
- Genomics data pipelines (VCF files, GATK, BWA, genome assembly workflows)
- Machine learning pipelines: MLflow, Kubeflow, or SageMaker for clinical model training
- Kubernetes / Docker containerization for data workloads
- Master's degree or PhD in Computer Science, Bioinformatics, or Biomedical Informatics
- Experience with Epic EHR, Cerner, or EPIC Clarity/Caboodle data models
- Snowflake data warehouse experience

Key Responsibilities:
- Architect the HealthAI multi-tenant clinical data platform serving 400+ hospital customers
- Design and maintain HIPAA-compliant data pipelines ingesting ADT, lab, radiology, and claims data
- Lead migration from legacy Oracle databases to AWS cloud data lake (S3 + Redshift)
- Build real-time clinical event streaming for patient deterioration early-warning ML models
- Mentor and grow a team of 4 data engineers through code reviews, architecture reviews, pairing
- Define data quality frameworks with SLA monitoring and automated alerting
- Collaborate with clinical informatics scientists on feature engineering for NLP and predictive models
"""

# ─────────────────────────────────────────────────────────────────────────────
# 10 Diverse Resumes: 5 for JD1 (PM/FinTech), 5 for JD2 (Data Eng/Healthcare)
# Varying quality: 2 excellent, 2 good, 1 weak for each JD
# ─────────────────────────────────────────────────────────────────────────────

RESUMES_JD1 = [
    # ── Resume 1: EXCELLENT PM — perfect match
    (
        "Priya_Sharma_PM.txt",
        """
Priya Sharma
priya.sharma@gmail.com | +1 (415) 892-3341 | San Francisco, CA
linkedin.com/in/priyasharmapm

PROFESSIONAL SUMMARY
Senior Product Manager with 8 years of experience in FinTech and payments, including 4 years at Stripe
building payment processing and fraud prevention products. Proven track record of taking products 0-to-1
and scaling to $500M+ GMV. Expert in ACH, card networks, real-time payments (RTP), and regulatory compliance.

WORK EXPERIENCE

Stripe — San Francisco, CA
Senior Product Manager, Payments Platform
2020 - Present
- Owned the Stripe Terminal product roadmap, growing from $20M to $350M GMV in 3 years
- Led a cross-functional team of 12 engineers, 3 designers, and compliance/legal to launch FedNow integration
- Wrote 40+ PRDs and worked directly with Visa/Mastercard networks on acceptance rate optimization
- Reduced merchant onboarding time from 7 days to 18 hours through automated KYC/AML workflows
- Defined OKRs and led quarterly product reviews with CTO and VP Product

PayPal — San Jose, CA
Product Manager, Fraud & Risk Management
2018 - 2020
- Built ML-powered fraud detection system reducing chargebacks by 31% across $2B monthly transaction volume
- Led PCI-DSS compliance audit for PayPal's card-not-present processing platform
- Designed REST APIs for merchant fraud webhook integrations (70+ merchant partners)
- Analyzed payment funnel data using SQL, Amplitude, and Tableau dashboards

Capital One — McLean, VA
Associate Product Manager
2016 - 2018
- Launched mobile banking payment features with 2.1M active monthly users
- Partnered with Compliance, Legal, and Finance on Reg E dispute resolution workflow

EDUCATION
Harvard Business School — MBA, Finance & Entrepreneurship — 2016
UC Berkeley — Bachelor of Science, Computer Science — 2014

SKILLS
Product Management, FinTech, Payments, ACH, Visa, Mastercard, Real-Time Payments (RTP), FedNow,
REST APIs, Fraud Detection, Risk Management, PCI-DSS Compliance, AML/KYC, SQL, Tableau, Amplitude,
Mixpanel, Agile, Scrum, PRDs, User Stories, OKRs, Stakeholder Management, Product Roadmap, BNPL,
ISO 20022, Cross-border Payments, Data Analysis, Python (basic), A/B Testing

CERTIFICATIONS
Certified Product Manager (CPM) — Product School 2019
PCI-DSS Implementation Certificate — 2021

ACHIEVEMENTS
- Grew Stripe Terminal to $350M GMV in 3 years from $20M launch baseline
- Launched FedNow real-time payment integration (first 10 FinTech companies in the US)
- Reduced merchant onboarding from 7 days to 18 hours
"""
    ),

    # ── Resume 2: GOOD PM — strong background but missing some FinTech depth
    (
        "Marcus_Williams_PM.txt",
        """
Marcus Williams
marcus.williams@email.com | +1 (312) 445-7890 | Chicago, IL
linkedin.com/in/marcuswilliamspm

SUMMARY
Product Manager with 7 years of experience leading SaaS and marketplace products. Strong in Agile delivery,
data-driven decision making, and cross-functional leadership. Recently pivoted to FinTech with 2 years at
a B2B payments startup. MBA from Booth School of Business.

WORK EXPERIENCE

PayNexus (B2B Payments Startup) — Chicago, IL
Product Manager
2022 - Present
- Led B2B invoice payment product from MVP to $85M GMV in 18 months
- Worked with engineering on REST API design for ERP (QuickBooks, SAP) integrations
- Collaborated with Compliance team on AML transaction monitoring workflows
- Analyzed funnel metrics using SQL and Mixpanel to improve ACH payment conversion by 22%

Salesforce — San Francisco, CA
Senior Product Manager, Salesforce Billing
2019 - 2022
- Owned billing and subscription management platform with 8,000+ enterprise customers
- Led cross-functional Agile team of 9 engineers and 2 UX designers
- Wrote detailed PRDs and managed quarterly roadmap planning and OKR setting
- Partnered with Finance, Legal, and Sales to launch EU billing compliance (GDPR)

McKinsey Digital — Chicago, IL
Associate Product Manager / Digital Consultant
2017 - 2019
- Delivered digital transformation projects for financial services and retail clients
- Conducted data analysis using SQL and Excel to identify revenue optimization opportunities

EDUCATION
University of Chicago Booth School of Business — MBA — 2017
University of Michigan — Bachelor of Arts, Economics — 2015

SKILLS
Product Management, SaaS, B2B Payments, ACH, REST APIs, AML Compliance, SQL, Mixpanel, Amplitude,
Agile, Scrum, PRDs, OKRs, Stakeholder Management, Roadmap Planning, Tableau, QuickBooks Integration,
Customer Discovery, Market Research, A/B Testing, Jira, Confluence

ACHIEVEMENTS
- Launched B2B invoice payment product reaching $85M GMV in 18 months
- Improved ACH payment conversion by 22% using funnel analysis
"""
    ),

    # ── Resume 3: GOOD PM — enterprise/tech focus, less payments depth
    (
        "Aisha_Patel_PM.txt",
        """
Aisha Patel
aisha.patel@outlook.com | +1 (617) 223-9988 | Boston, MA
linkedin.com/in/aishapatelpm

PROFESSIONAL SUMMARY
Product Manager with 6 years in enterprise SaaS and platform products. Strong technical background
(engineering degree), excellent at writing PRDs, working with distributed engineering teams, and
using data to drive product decisions. Looking to deepen FinTech expertise.

WORK EXPERIENCE

HubSpot — Cambridge, MA
Product Manager, Platform & Integrations
2021 - Present
- Owned the HubSpot App Marketplace platform product (5,000+ integrations)
- Designed REST API standards and developer experience documentation
- Led Agile sprints with 8 engineers; wrote 50+ PRDs and user stories
- Used Amplitude, SQL, and Tableau to track activation metrics and DAU/MAU

Wayfair — Boston, MA
Associate Product Manager, Checkout & Payments
2019 - 2021
- Co-owned Wayfair checkout flow with $3B annual GMV processed through Visa/Mastercard networks
- Worked with Risk team on fraud detection rules for card-not-present transactions
- Collaborated with Legal and Compliance on PCI scope reduction initiatives
- Analyzed payment failure rates with SQL and partnered with engineering to improve by 18%

Accenture — Boston, MA
Business Analyst
2018 - 2019
- Delivered process improvement projects for banking and insurance clients

EDUCATION
MIT — Bachelor of Science, Electrical Engineering and Computer Science — 2018

SKILLS
Product Management, SaaS Platform, REST APIs, Payments, Visa, Mastercard, Fraud Detection,
PCI-DSS, SQL, Amplitude, Tableau, Agile, Scrum, PRDs, Roadmap, OKRs, Jira, Confluence,
Stakeholder Management, A/B Testing, Developer Experience, API Design, Customer Research

CERTIFICATIONS
AWS Certified Cloud Practitioner — 2022
"""
    ),

    # ── Resume 4: MODERATE PM — general PM background, limited payments experience
    (
        "Jake_Thompson_PM.txt",
        """
Jake Thompson
jake.thompson@gmail.com | +1 (323) 556-4231 | Los Angeles, CA

PROFESSIONAL SUMMARY
Product Manager with 5 years of experience in consumer apps and mobile products.
Good at user research, roadmap planning, and working with design and engineering teams.
Interested in expanding into FinTech.

WORK EXPERIENCE

Spotify — Los Angeles, CA
Product Manager, Consumer Mobile
2021 - Present
- Managed the Spotify social listening features and playlist curation tools
- Ran user research sessions and A/B tests to improve engagement metrics
- Wrote PRDs and worked with 6 engineers in Agile sprints

DoorDash — San Francisco, CA
Associate Product Manager, Consumer
2019 - 2021
- Worked on the DoorDash consumer app checkout experience
- Collaborated with Engineering on performance improvements reducing app load time by 30%
- Used Mixpanel and Amplitude for funnel analysis

EDUCATION
UCLA — Bachelor of Arts, Business Administration — 2019

SKILLS
Product Management, Mobile Apps, Agile, Scrum, PRDs, User Research, A/B Testing,
Mixpanel, Amplitude, SQL (basic), Stakeholder Management, Roadmap Planning, Jira, Figma

ACHIEVEMENTS
- Improved DoorDash checkout conversion rate by 8% through UX optimization
"""
    ),

    # ── Resume 5: WEAK PM — mismatched background (healthcare PM, no payments)
    (
        "Sarah_Chen_PM.txt",
        """
Sarah Chen
sarah.chen@gmail.com | +1 (503) 778-2211 | Portland, OR

PROFESSIONAL SUMMARY
Product Manager with 5 years in healthcare SaaS and clinical workflow products.
Experience with HIPAA compliance, EHR integrations, and clinical user research.

WORK EXPERIENCE

Epic Systems — Verona, WI
Product Manager, Clinical Workflows
2021 - Present
- Managed Epic EHR physician workflow optimization products
- Led integration projects with FHIR APIs and HL7 v2 clinical data feeds
- Wrote PRDs and worked with clinical informatics teams

Cerner — Kansas City, MO
Business Analyst, Clinical Analytics
2019 - 2021
- Developed clinical data analysis dashboards using SQL and Tableau
- Worked with hospital compliance teams on HIPAA audit reporting

EDUCATION
Johns Hopkins University — Master of Public Health — 2019
University of Oregon — Bachelor of Science, Biology — 2017

SKILLS
Product Management, Healthcare SaaS, HIPAA, EHR, FHIR APIs, HL7, SQL, Tableau,
Clinical Workflows, Agile, PRDs, Stakeholder Management, Compliance

ACHIEVEMENTS
- Led Epic EHR integration for 3 major hospital networks
"""
    ),
]

RESUMES_JD2 = [
    # ── Resume 6: EXCELLENT Data Engineer — perfect match for JD2
    (
        "Rahul_Krishnamurthy_DE.txt",
        """
Rahul Krishnamurthy
rahul.k@gmail.com | +1 (512) 334-7823 | Austin, TX
linkedin.com/in/rahulk | github.com/rahulk-data

PROFESSIONAL SUMMARY
Principal Data Engineer with 10 years of experience building large-scale healthcare data platforms.
Deep expertise in HIPAA-compliant data engineering, Apache Spark, FHIR R4, AWS cloud, and leading
high-performing data engineering teams in clinical and life sciences organizations.

WORK EXPERIENCE

Optum (UnitedHealth Group) — Austin, TX
Principal Data Engineer, Clinical Data Platform
2019 - Present
- Architected HIPAA-compliant data lake on AWS (S3, Glue, Redshift, EMR) processing 120TB/day clinical data
- Built PySpark pipelines transforming HL7 v2, FHIR R4, ICD-10, CPT codes, and LOINC data at petabyte scale
- Designed Apache Airflow orchestration for 200+ clinical ETL pipelines with SLA monitoring
- Led migration from Oracle to AWS cloud data lake reducing query costs by 68%
- Implemented Delta Lake architecture for ACID transactions on healthcare data
- Mentored and managed team of 5 data engineers through code reviews and architecture design sessions
- Built real-time Kafka streaming pipeline for patient deterioration early-warning signals
- Ensured PHI data security with encryption at rest/transit, audit logging, and data masking per HIPAA
- Used dbt for 300+ data transformations with full lineage documentation

Epic Systems — Madison, WI
Senior Data Engineer, Data Infrastructure
2016 - 2019
- Built FHIR R4 data ingestion pipelines for Epic Clarity and Caboodle data models
- Developed Python ETL frameworks for clinical data feeds from 150+ hospital Epic instances
- Implemented Apache Kafka streaming for real-time ADT (admit/discharge/transfer) event processing
- Designed PostgreSQL schemas for clinical analytics data warehouse

Deloitte Analytics — Chicago, IL
Data Engineer
2014 - 2016
- Built Big Data pipelines using Apache Spark on Hadoop for financial services clients
- Developed Python ETL automation scripts and SQL stored procedures

EDUCATION
University of Texas at Austin — Master of Science, Computer Science — 2014
Indian Institute of Technology (IIT Bombay) — Bachelor of Technology, Computer Science — 2012

SKILLS
Python, PySpark, Apache Spark, Apache Airflow, Apache Kafka, SQL, PostgreSQL, AWS (S3, Glue,
Redshift, EMR, Kinesis), FHIR R4, HL7 v2, ICD-10, CPT codes, LOINC, HIPAA Compliance, PHI Security,
Data Lake Architecture, Delta Lake, Apache Iceberg, dbt, Docker, Kubernetes, MLflow, Snowflake,
Data Quality, SLA Monitoring, ETL, Data Modeling, Healthcare Data, Clinical Informatics, BigQuery,
Team Leadership, Technical Mentorship, Code Review, Architecture Design, Epic EHR, Cerner

CERTIFICATIONS
AWS Certified Data Analytics Specialty — 2021
AWS Certified Solutions Architect — Professional — 2020
HIPAA Privacy and Security Certified — 2019

ACHIEVEMENTS
- Built HIPAA data lake processing 120TB/day reducing query costs by 68% vs Oracle legacy
- Led team of 5 engineers delivering patient early-warning streaming system now used by 80 hospitals
- Migrated 8-year clinical historical dataset (2PB) from Oracle to AWS with zero data loss
"""
    ),

    # ── Resume 7: GOOD Data Engineer — strong AWS/Spark but limited healthcare
    (
        "Mei_Lin_DataEng.txt",
        """
Mei Lin
mei.lin@techmail.com | +1 (206) 887-4412 | Seattle, WA
linkedin.com/in/meilin-de | github.com/meilindata

PROFESSIONAL SUMMARY
Senior Data Engineer with 8 years of experience in large-scale data platforms across e-commerce
and financial services. Expert in Python, PySpark, AWS, Apache Airflow, Kafka, and dbt.
Currently transitioning toward healthcare data — pursuing HIPAA training.

WORK EXPERIENCE

Amazon (AWS Marketplace) — Seattle, WA
Senior Data Engineer, Commerce Analytics
2020 - Present
- Built PySpark data pipelines processing 80TB/day seller transaction data on AWS EMR
- Architected Redshift data warehouse with dbt transformations for 500+ business metrics
- Implemented Apache Airflow DAGs orchestrating 150+ pipelines with monitoring and alerting
- Built real-time Kafka streaming for seller fraud event detection
- Led migration to Delta Lake on S3 for ACID compliance on analytics datasets
- Mentored 3 junior data engineers in code quality and architecture best practices

JPMorgan Chase — New York, NY
Data Engineer, Risk Analytics Platform
2017 - 2020
- Built Python ETL pipelines ingesting trading and risk data from 40+ upstream systems
- Developed PostgreSQL schemas and SQL analytics queries for regulatory reporting
- Implemented AWS Glue and S3 data lake for trade surveillance data

Infosys — Hyderabad, India
Software Engineer, Data
2016 - 2017
- Developed Hadoop MapReduce jobs and Hive queries for banking clients

EDUCATION
University of Washington — Master of Science, Data Science — 2016
Tsinghua University — Bachelor of Engineering, Software Engineering — 2014

SKILLS
Python, PySpark, Apache Spark, Apache Airflow, Apache Kafka, SQL, PostgreSQL, AWS (S3, EMR,
Glue, Redshift, Kinesis), dbt, Delta Lake, Apache Iceberg, Docker, Kubernetes, BigQuery,
Data Quality, ETL, Data Modeling, Financial Services Data, REST APIs, Snowflake, MLflow

CERTIFICATIONS
AWS Certified Data Analytics Specialty — 2022
AWS Certified Solutions Architect — Associate — 2021
"""
    ),

    # ── Resume 8: GOOD Data Engineer — healthcare domain but less Spark/cloud depth
    (
        "David_Okonkwo_DataEng.txt",
        """
David Okonkwo
david.okonkwo@email.com | +1 (469) 334-9087 | Dallas, TX
linkedin.com/in/davidokonkwo

PROFESSIONAL SUMMARY
Data Engineer with 7 years of experience in healthcare and clinical data systems.
Strong in FHIR, HL7 v2, HIPAA compliance, and clinical data modeling. Building cloud
migration skills with recent AWS training and Airflow experience.

WORK EXPERIENCE

Children's Medical Center Dallas — Dallas, TX
Senior Data Engineer, Clinical Analytics
2020 - Present
- Built Python ETL pipelines for FHIR R4 and HL7 v2 clinical data feeds from Epic EHR
- Developed SQL data models for ICD-10, CPT code, and LOINC lab result analytics
- Implemented HIPAA-compliant data masking and PHI audit logging using PostgreSQL
- Built Apache Airflow pipelines for nightly clinical data warehouse refresh
- Collaborated with clinical informatics scientists on patient risk stratification models
- Designed FHIR Bulk Export APIs for population health analytics platform

Cerner Corporation — Kansas City, MO
Data Engineer, Health Data Exchange
2017 - 2020
- Developed HL7 v2 ADT message parsing and routing infrastructure in Python
- Built SQL Server data warehouse for clinical quality metrics (HEDIS, CMS)
- Implemented CDC (Change Data Capture) pipelines from Cerner Millennium database

Cognizant — Dallas, TX
Software Developer
2016 - 2017
- Developed Java backend services for insurance claims processing platform

EDUCATION
University of Texas at Dallas — Master of Science, Information Systems — 2016
University of Lagos — Bachelor of Science, Computer Science — 2014

SKILLS
Python, SQL, PostgreSQL, FHIR R4, HL7 v2, ICD-10, CPT, LOINC, HIPAA Compliance, PHI Data Security,
Apache Airflow, Epic EHR, Cerner, ETL, Data Modeling, Clinical Data Warehouse, Data Quality,
AWS (S3, Glue — learning), Apache Kafka (basic), PySpark (learning), dbt, Power BI

CERTIFICATIONS
HIPAA Privacy and Security Certified — 2020
AWS Certified Cloud Practitioner — 2023
HL7 FHIR Certified Developer — 2021
"""
    ),

    # ── Resume 9: MODERATE Data Engineer — general data eng, no healthcare
    (
        "Alex_Rivera_DataEng.txt",
        """
Alex Rivera
alex.rivera@gmail.com | +1 (415) 228-4499 | San Francisco, CA

SUMMARY
Data Engineer with 6 years building data pipelines and analytics infrastructure.
Strong Python and SQL skills. Experience with Spark, Airflow, and cloud platforms.

WORK EXPERIENCE

Lyft — San Francisco, CA
Data Engineer, Rides Analytics
2020 - Present
- Built PySpark data pipelines processing 15TB/day rideshare transaction data on AWS
- Maintained Apache Airflow pipeline orchestration for 80+ data workflows
- Developed dbt models for BI reporting with Looker
- Collaborated with ML engineers on feature pipelines for driver churn prediction

Twitter / X — San Francisco, CA
Data Engineer
2018 - 2020
- Developed Apache Kafka streaming pipelines for real-time ad impression data
- Built Python ETL scripts for social media analytics data warehouse (PostgreSQL)

EDUCATION
University of California, Davis — Bachelor of Science, Statistics — 2018

SKILLS
Python, PySpark, Apache Airflow, Apache Kafka, SQL, PostgreSQL, AWS (S3, EMR, Redshift),
dbt, Looker, Data Modeling, ETL, Data Quality, Machine Learning Pipelines, Spark

ACHIEVEMENTS
- Built ride data pipeline processing 15TB/day with 99.9% uptime SLA
"""
    ),

    # ── Resume 10: WEAK Data Engineer — junior, wrong domain (marketing analytics)
    (
        "Emma_Johnson_Analytics.txt",
        """
Emma Johnson
emma.johnson@gmail.com | +1 (212) 445-8832 | New York, NY

PROFESSIONAL SUMMARY
Data Analyst transitioning to Data Engineering with 4 years in marketing analytics.
Strong SQL and Python skills, learning Spark and cloud technologies.

WORK EXPERIENCE

Unilever — New York, NY
Senior Data Analyst, Marketing Analytics
2021 - Present
- Built SQL dashboards and Tableau reports for marketing campaign performance
- Automated Python data extraction scripts from Facebook Ads, Google Analytics APIs
- Collaborated with Data Engineering team to improve data pipeline reliability

Publicis Groupe — New York, NY
Data Analyst
2019 - 2021
- Analyzed digital ad performance data using SQL and Excel
- Created Tableau dashboards for client reporting

EDUCATION
New York University — Bachelor of Science, Business Analytics — 2019

SKILLS
SQL, Python (Pandas, basic), Tableau, Excel, Google Analytics, Facebook Ads API,
Data Analysis, Marketing Analytics, Salesforce, Looker (basic), AWS S3 (learning)

CERTIFICATIONS
Google Data Analytics Professional Certificate — 2022
"""
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Color helpers for terminal output
# ─────────────────────────────────────────────────────────────────────────────
def c(text, code): return f"\033[{code}m{text}\033[0m"
def bold(t): return c(t, "1")
def green(t): return c(t, "32")
def yellow(t): return c(t, "33")
def red(t): return c(t, "31")
def cyan(t): return c(t, "36")
def magenta(t): return c(t, "35")
def blue(t): return c(t, "34")
def dim(t): return c(t, "2")

def score_color(score: float) -> str:
    if score >= 80:
        return green(f"{score:.1f}")
    elif score >= 60:
        return yellow(f"{score:.1f}")
    else:
        return red(f"{score:.1f}")

def rank_badge(rank: int) -> str:
    if rank == 1: return "🥇"
    if rank == 2: return "🥈"
    if rank == 3: return "🥉"
    return f"#{rank}"


async def login(client: httpx.AsyncClient) -> str:
    """Login and return auth token."""
    resp = await client.post(f"{BASE_URL}/auth/login", json={
        "email": LOGIN_EMAIL, "password": LOGIN_PASS
    })
    if resp.status_code != 200:
        print(red(f"❌ Login failed: {resp.status_code} — {resp.text[:200]}"))
        sys.exit(1)
    token = resp.json()["access_token"]
    print(green(f"✅ Logged in as {LOGIN_EMAIL}"))
    return token


async def parse_and_create_job(client: httpx.AsyncClient, headers: dict, jd_text: str, jd_num: int) -> Optional[dict]:
    """Parse JD text → show extracted info → save job."""
    print(f"\n{bold(cyan(f'═══ JD {jd_num}: Parsing & Extracting with AI ═══'))}")

    # Step 1: Parse
    resp = await client.post(f"{BASE_URL}/jobs/parse-text",
                              json={"raw_description": jd_text}, headers=headers)
    if resp.status_code != 200:
        print(red(f"❌ JD parse failed: {resp.status_code} — {resp.text[:300]}"))
        return None

    parsed = resp.json()
    print(f"  {bold('Role:')} {parsed.get('role', 'N/A')}")
    print(f"  {bold('Department:')} {parsed.get('department', 'N/A')}")
    print(f"  {bold('Experience:')} {parsed.get('min_experience_years', 0)}–{parsed.get('max_experience_years', 0)} years")
    print(f"  {bold('Location:')} {parsed.get('location', 'N/A')} | Remote: {parsed.get('is_remote', False)}")
    print(f"  {bold('Salary:')} {parsed.get('salary_currency', 'USD')} {parsed.get('min_salary', 0):,.0f} – {parsed.get('max_salary', 0):,.0f}")
    print(f"  {bold('Education:')} {parsed.get('education_requirement', 'N/A')}")

    mand = parsed.get("mandatory_skills", [])
    good = parsed.get("good_to_have_skills", [])
    mand_names = [s["name"] if isinstance(s, dict) else s for s in mand]
    good_names = [s["name"] if isinstance(s, dict) else s for s in good]
    print(f"  {bold(blue(f'Mandatory Skills ({len(mand_names)})'))}: {', '.join(mand_names[:12])}")
    if good_names:
        print(f"  {bold(magenta(f'Nice-to-Have ({len(good_names)})'))}: {', '.join(good_names[:8])}")

    responsibilities = parsed.get("responsibilities", [])
    if responsibilities:
        print(f"  {bold('Responsibilities ({})'.format(len(responsibilities)))}:")
        for r in responsibilities[:3]:
            print(f"    • {dim(r)}")

    # Step 2: Save the job
    save_payload = {
        "title": parsed.get("role", f"Job {jd_num}"),
        "department": parsed.get("department", "General"),
        "raw_description": jd_text,
        "status": "active",
        "min_experience_years": parsed.get("min_experience_years") or 0,
        "max_experience_years": parsed.get("max_experience_years") or 10,
        "education_requirement": parsed.get("education_requirement") or "",
        "location": parsed.get("location") or "",
        "is_remote": parsed.get("is_remote") or False,
        "min_salary": parsed.get("min_salary"),
        "max_salary": parsed.get("max_salary"),
        "salary_currency": parsed.get("salary_currency") or "USD",
        "responsibilities": parsed.get("responsibilities") or [],
        "mandatory_skills": mand[:25],
        "good_to_have_skills": good[:10],
    }

    resp2 = await client.post(f"{BASE_URL}/jobs/", json=save_payload, headers=headers)
    if resp2.status_code != 201:
        print(red(f"❌ Job save failed: {resp2.status_code} — {resp2.text[:300]}"))
        return None

    job = resp2.json()
    job_id = job["id"]
    print(green(f"  ✅ Job saved: ID = {job_id}"))
    return job


async def upload_resume_text(client: httpx.AsyncClient, headers: dict, job_id: str,
                              filename: str, resume_text: str, idx: int, total: int) -> Optional[dict]:
    """Upload a resume as a text file and return the parsed resume data."""
    print(f"  [{idx}/{total}] Uploading {bold(filename)}...", end="", flush=True)

    file_bytes = resume_text.strip().encode("utf-8")
    files = {
        "file": (filename, io.BytesIO(file_bytes), "text/plain"),
    }
    data = {"job_id": job_id}

    resp = await client.post(
        f"{BASE_URL}/resumes/upload",
        files=files,
        data=data,
        headers={k: v for k, v in headers.items() if k != "Content-Type"},
        timeout=60.0,
    )

    if resp.status_code == 201:
        resume = resp.json()
        candidate_name = (resume.get("parsed_data") or {}).get("name", filename.replace(".txt", ""))
        exp = (resume.get("parsed_data") or {}).get("total_experience_years", 0)
        skills = (resume.get("parsed_data") or {}).get("skills", [])
        print(f" {green('✅')} {bold(candidate_name)} | {exp}yrs exp | {len(skills)} skills extracted")
        return resume
    else:
        print(f" {red('❌')} Failed: {resp.status_code} — {resp.text[:150]}")
        return None


async def get_rankings(client: httpx.AsyncClient, headers: dict, job: dict) -> list:
    """Fetch scored + ranked candidates for a job."""
    job_id = job["id"]
    job_title = job["title"]

    print(f"\n{bold(cyan('⏳ Computing AI Scores & Rankings for:'))} {yellow(job_title)}")
    print(dim("  (Evaluating all candidates: mandatory skills, experience, industry, education, certifications, location...)"))

    resp = await client.get(
        f"{BASE_URL}/dashboard/job/{job_id}/candidates",
        headers=headers,
        timeout=120.0,
    )

    if resp.status_code != 200:
        print(red(f"❌ Rankings fetch failed: {resp.status_code} — {resp.text[:300]}"))
        return []

    return resp.json()


def print_ranking_table(cards: list, job: dict):
    """Print a beautiful formatted ranking table."""
    job_title = job["title"]
    job_id = job["id"]
    mand_skills = [s["name"] if isinstance(s, dict) else s
                   for s in (job.get("parsed_data") or {}).get("mandatory_skills", [])]

    print(f"\n{'═'*90}")
    print(f"  {bold(magenta('AI CANDIDATE RANKING LEADERBOARD'))}")
    print(f"  {bold('Job:')} {yellow(job_title)} | ID: {dim(job_id[:8]+'...')}")
    if mand_skills:
        print(f"  {bold('Mandatory Skills:')} {', '.join(mand_skills[:8])}")
    print(f"{'═'*90}\n")

    header = (
        f"  {'RANK':<6} {'CANDIDATE':<26} {'SCORE':>7} {'EXP':>6} "
        f"{'SKILLS%':>8} {'INDUSTRY':>9} {'EXP%':>6} {'FIT':<14}"
    )
    print(bold(header))
    print(dim("  " + "─"*86))

    for rank, card in enumerate(cards, 1):
        name = card.get("full_name", "Unknown")[:24]
        score = card.get("overall_score", 0)
        exp = card.get("total_experience_years", 0) or 0
        breakdown = card.get("score_breakdown") or {}

        mand_pct = (breakdown.get("mandatory_skills") or {}).get("raw_score", 0)
        ind_pct = (breakdown.get("industry_match") or {}).get("raw_score", 0)
        exp_pct = (breakdown.get("experience") or {}).get("raw_score", 0)

        # Fit label
        if score >= 80:
            fit = green("🟢 Strong Fit")
        elif score >= 65:
            fit = yellow("🟡 Good Fit")
        elif score >= 50:
            fit = yellow("🟠 Moderate Fit")
        else:
            fit = red("🔴 Weak Fit")

        badge = rank_badge(rank)
        print(
            f"  {badge:<6} {bold(name):<26} {score_color(score):>16} "
            f"{exp:>5.1f}y {score_color(mand_pct):>17} {score_color(ind_pct):>18} "
            f"{score_color(exp_pct):>15}  {fit}"
        )

        # Summary line
        summary = card.get("summary_text", "")
        if summary:
            truncated = summary[:105] + "..." if len(summary) > 105 else summary
            print(f"         {dim(truncated)}")

        # Score breakdown detail for top 3
        if rank <= 3 and breakdown:
            mand_r = breakdown.get("mandatory_skills", {}).get("reasoning", "")
            nice_r = breakdown.get("nice_to_have_skills", {}).get("reasoning", "")
            if mand_r:
                print(f"         {dim('→ Skills: ')}{dim(mand_r[:120])}")
            if nice_r:
                print(f"         {dim('→ Bonus: ')}{dim(nice_r[:100])}")

        print()

    print(dim("  " + "─"*86))
    print(f"\n  {bold('Score Weights:')} Mandatory Skills 40% | Experience 20% | Nice-to-Have 10% | Career Stability 10% | Industry 8% | Education 5% | Certs 4% | Location 3%\n")


async def main():
    print(f"\n{'='*90}")
    print(f"  {bold(cyan('🤖  AI RESUME SCREENER — End-to-End Test'))}")
    print(f"  {bold('Testing:')} 2 Complex JDs × 10 Diverse Resumes → Ranked Leaderboard")
    print(f"{'='*90}\n")

    async with httpx.AsyncClient(timeout=90.0) as client:
        # ── Login ──
        token = await login(client)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # ═══ JOB 1: Senior Product Manager — FinTech/Payments ═══════════════
        print(f"\n{'─'*90}")
        print(f"  {bold(blue('JOB 1 OF 2: Senior Product Manager – Payments & FinTech Platform'))}")
        print(f"{'─'*90}")

        job1 = await parse_and_create_job(client, headers, JD_1, 1)
        if not job1:
            print(red("Could not create JD 1. Exiting.")); sys.exit(1)

        print(f"\n{bold(cyan('📎 Uploading 5 PM Candidate Resumes for JD 1...'))} \n")
        upload_headers = {"Authorization": f"Bearer {token}"}
        for i, (fname, rtext) in enumerate(RESUMES_JD1, 1):
            await upload_resume_text(client, upload_headers, job1["id"], fname, rtext, i, len(RESUMES_JD1))
            await asyncio.sleep(0.5)

        cards1 = await get_rankings(client, headers, job1)
        if cards1:
            print_ranking_table(cards1, job1)

        # ═══ JOB 2: Principal Data Engineer — Healthcare/Clinical ════════════
        print(f"\n{'─'*90}")
        print(f"  {bold(blue('JOB 2 OF 2: Principal Data Engineer – Clinical Analytics & Healthcare'))}")
        print(f"{'─'*90}")

        job2 = await parse_and_create_job(client, headers, JD_2, 2)
        if not job2:
            print(red("Could not create JD 2. Exiting.")); sys.exit(1)

        print(f"\n{bold(cyan('📎 Uploading 5 Data Engineering Candidate Resumes for JD 2...'))} \n")
        for i, (fname, rtext) in enumerate(RESUMES_JD2, 1):
            await upload_resume_text(client, upload_headers, job2["id"], fname, rtext, i, len(RESUMES_JD2))
            await asyncio.sleep(0.5)

        cards2 = await get_rankings(client, headers, job2)
        if cards2:
            print_ranking_table(cards2, job2)

        # ═══ SUMMARY ══════════════════════════════════════════════════════════
        print(f"\n{'═'*90}")
        print(f"  {bold(green('✅ TEST COMPLETE — AI Ranking Summary'))}")
        print(f"{'═'*90}")
        print(f"  {bold('JD 1 — Senior PM / FinTech:')} {len(cards1)} candidates ranked")
        if cards1:
            top1 = cards1[0]
            print(f"    🥇 Top Candidate: {bold(top1['full_name'])} | Score: {green(str(top1['overall_score']))} | {top1['total_experience_years']}yrs exp")
        print(f"  {bold('JD 2 — Principal Data Engineer / Healthcare:')} {len(cards2)} candidates ranked")
        if cards2:
            top2 = cards2[0]
            print(f"    🥇 Top Candidate: {bold(top2['full_name'])} | Score: {green(str(top2['overall_score']))} | {top2['total_experience_years']}yrs exp")
        print(f"\n  {dim('View full dashboard at http://localhost:3000')}\n")


if __name__ == "__main__":
    asyncio.run(main())
