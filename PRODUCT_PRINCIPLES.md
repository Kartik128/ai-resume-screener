# Product Principles & Operating Philosophy

This document serves as the shared definition of what belongs in the TalentAI platform and how it should be built. Every architectural, design, database, and feature decision must align with these core tenets.

---

## 1. Product Vision

We are **NOT** building another Applicant Tracking System (ATS). We are building an **AI Hiring Intelligence Platform**.

Our mission:
> **Help organizations identify, evaluate, and hire the best talent significantly faster through explainable AI while keeping recruiters fully in control.**

Every new capability must save recruiter time, improve hiring quality, increase confidence, or maintain recruiter trust. If it does not, it does not belong in the product.

---

## 2. Engineering Philosophy

We optimize continuously for:
* **Simplicity**: Prefer the simpler solution. Avoid over-engineering.
* **Scalability**: Design for tenant isolation, millions of users, and billions of rows.
* **Reliability**: Use background job queues, rate limiting, and defensive database indexes.
* **Maintainability**: Low coupling, high cohesion, modules are easily replaceable.
* **Explainability**: AI recommendations must never behave as a black box.
* **Security**: Enforce role-based access control, tenant isolation, and audit logs.

---

## 3. Product Tier Priorities

Features must be prioritized strictly according to their tier:

### 🏆 Tier 1: Core AI Intelligence (Highest Priority)
- Resume Parsing & Structured Intelligence
- Candidate Ranking & Explanation Engine
- Candidate Comparison & Recruiter Copilot
- Candidate Rediscovery
- Interview Transcript Intelligence
- AI Recommendation Engine

### ⚖️ Tier 2: Workflow & Recruitment Operations
- Pipeline & ATS Workflow Management
- Candidate Portal & Assessments
- Integrations (Email, Calendars)
- Performance Analytics

### 💤 Tier 3: Secondary Lifecycle (Lowest Priority)
- Workforce Planning & Forecasting
- Succession Planning & Internal Mobility
- Advanced Employee Lifecycle Analytics

*Note: Never let Tier 3 operations compromise or delay progress on Tier 1 excellence.*

---

## 4. AI & Human-in-the-Loop Principles

1. **AI Recommends, Humans Decide**: The AI never automatically rejects or hires candidates. The recruiter makes all final decisions.
2. **Transparent Recommendations**: Every score must detail matched skills, missing skills, career stability indicators, confidence scores, and potential hiring risks.
3. **Continuous Learning**: Recruiters' override decisions must be logged and evaluated to improve future AI matching metrics.

---

## 5. Architectural Standards

* **Tenant Isolation**: Strict check of company context mapping on every SQL query. Recruiter from Company A must never query files of Company B.
* **AI Provider Agnosticism**: AI prompt adapters must remain decoupled so that underlying LLMs (OpenAI, Gemini, local models) can be swapped seamlessly.
* **Observability**: Latency (API, DB, AI tokens) and processing sizes must be continuously monitored and logged.
