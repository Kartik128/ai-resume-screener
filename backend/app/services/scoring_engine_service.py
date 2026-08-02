from typing import Any, Dict, List, Optional
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.matching import SemanticMatchRequest
from app.schemas.scoring import ComponentScore, ScoreBreakdownResponse
from app.services.semantic_matcher_service import SemanticMatcherService

# Default scoring weights — used when no recruiter scorecard is set
DEFAULT_WEIGHTS = {
    "mandatory_skills": 40.0,
    "experience": 20.0,
    "nice_to_have": 10.0,
    "career_stability": 10.0,
    "industry_match": 8.0,
    "education": 5.0,
    "certifications": 4.0,
    "location": 3.0,
}


class ScoringEngineService:
    """Explainable AI Candidate Scoring Engine implementing 100-point weighted allocation.

    Weights are read from recruiter scorecard if available, otherwise defaults apply:
    - Mandatory Skills Match:   40%  (most critical — direct alignment with JD requirements)
    - Experience Depth:         20%  (years and relevance of experience)
    - Nice-To-Have Skills:      10%  (bonus skills alignment)
    - Career Stability:         10%  (average tenure per role)
    - Industry Domain Match:     8%  (industry/domain experience relevance)
    - Education Fit:             5%  (degree alignment with JD requirements)
    - Certifications:            4%  (professional certifications match)
    - Location:                  3%  (location / remote work alignment)
    """

    @staticmethod
    async def evaluate_candidate(
        job: Job,
        resume: Resume,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> ScoreBreakdownResponse:
        # Merge custom weights with defaults
        W = {**DEFAULT_WEIGHTS, **(custom_weights or {})}
        # Normalise to fractions
        w_mand  = W["mandatory_skills"] / 100.0
        w_exp   = W["experience"] / 100.0
        w_nice  = W["nice_to_have"] / 100.0
        w_stab  = W["career_stability"] / 100.0
        w_ind   = W["industry_match"] / 100.0
        w_edu   = W["education"] / 100.0
        w_cert  = W["certifications"] / 100.0
        w_loc   = W["location"] / 100.0

        parsed_job = job.parsed_data or {}
        parsed_resume = resume.parsed_data or {}

        # Candidate skill names for matching
        cand_skills = [s.get("name", "") for s in parsed_resume.get("skills", []) if s.get("name")]
        cand_exp_text = resume.raw_text or ""

        # ─── 1. Mandatory Skills Score (40%) ───────────────────────────────────
        mandatory_req = parsed_job.get("mandatory_skills", [])
        mandatory_req_names = [s.get("name", s) if isinstance(s, dict) else s for s in mandatory_req]

        matched_count = 0
        missing_skills_list = []
        if mandatory_req_names:
            match_req = SemanticMatchRequest(
                required_skills=mandatory_req_names,
                candidate_skills=cand_skills,
                candidate_experience_text=cand_exp_text,
            )
            match_res = await SemanticMatcherService.match_skills(match_req)
            mand_raw = match_res.overall_semantic_score
            matched_count = sum(1 for m in match_res.semantic_matches if m.match_type.value != "MISSING")
            missing = [m.required_skill for m in match_res.semantic_matches if m.match_type.value == "MISSING"]
            missing_skills_list = missing
            mand_reasoning = (
                f"Matched {matched_count}/{len(mandatory_req_names)} mandatory skills. "
                + (f"Missing: {', '.join(missing[:5])}." if missing else "All mandatory skills present or semantically matched.")
            )
        else:
            mand_raw = 100.0
            mand_reasoning = "No mandatory skills specified in job posting."

        # Map citations from semantic matches
        mand_citations = []
        if mandatory_req_names and 'match_res' in locals():
            mand_citations = [
                {
                    "required_skill": m.required_skill,
                    "matched_candidate_skill": m.matched_candidate_skill,
                    "evidence_sentence": m.evidence_sentence,
                    "char_start": m.char_start,
                    "char_end": m.char_end,
                }
                for m in match_res.semantic_matches
                if m.evidence_sentence
            ]

        mand_score = ComponentScore(
            weight_percentage=W["mandatory_skills"],
            raw_score=round(mand_raw, 1),
            weighted_score=round(mand_raw * w_mand, 2),
            reasoning=mand_reasoning,
            citations=mand_citations,
        )

        # ─── 2. Experience Depth Score (20%) ───────────────────────────────────
        cand_exp_years = float(parsed_resume.get("total_experience_years") or 0.0)
        req_min_exp = float(job.min_experience_years or 0.0)
        req_max_exp = float(job.max_experience_years or 99.0)

        if req_min_exp == 0.0:
            exp_raw = 100.0
            exp_reasoning = f"No minimum experience requirement. Candidate has {cand_exp_years} years."
        elif req_max_exp > 0 and cand_exp_years > req_max_exp:
            excess = cand_exp_years - req_max_exp
            exp_raw = max(60.0, 90.0 - (excess * 5.0))
            exp_reasoning = f"Overqualified candidate: Has {cand_exp_years} years, which is above the target range of {req_min_exp}–{req_max_exp} years (overqualified by {round(excess, 1)} years)."
        elif cand_exp_years >= req_min_exp:
            # Proportional score within the target band
            band = max(1.0, req_max_exp - req_min_exp)
            exp_raw = 85.0 + (15.0 * (cand_exp_years - req_min_exp) / band)
            exp_reasoning = f"Candidate has {cand_exp_years} years — within required range of {req_min_exp}–{req_max_exp} years."
        elif cand_exp_years >= req_min_exp * 0.7:
            exp_raw = 60.0 + (25.0 * (cand_exp_years / req_min_exp))
            exp_reasoning = f"Underqualified candidate: Candidate has {cand_exp_years} years — slightly below required minimum of {req_min_exp} years."
        else:
            exp_raw = max(20.0, (cand_exp_years / req_min_exp) * 60.0) if req_min_exp > 0 else 50.0
            exp_reasoning = f"Underqualified candidate: Experience gap. Candidate has {cand_exp_years} years vs {req_min_exp} years required."

        exp_score = ComponentScore(
            weight_percentage=W["experience"],
            raw_score=round(min(exp_raw, 100.0), 1),
            weighted_score=round(min(exp_raw, 100.0) * w_exp, 2),
            reasoning=exp_reasoning,
        )

        # ─── 3. Nice-To-Have Skills Score (10%) ────────────────────────────────
        nice_req = parsed_job.get("good_to_have_skills", [])
        nice_req_names = [s.get("name", s) if isinstance(s, dict) else s for s in nice_req]

        if nice_req_names:
            match_req = SemanticMatchRequest(
                required_skills=nice_req_names,
                candidate_skills=cand_skills,
                candidate_experience_text=cand_exp_text,
            )
            match_res = await SemanticMatcherService.match_skills(match_req)
            nice_raw = match_res.overall_semantic_score
            nice_matched = sum(1 for m in match_res.semantic_matches if m.match_type.value != "MISSING")
            nice_reasoning = f"Matched {nice_matched}/{len(nice_req_names)} preferred/bonus skills."
        else:
            nice_raw = 100.0
            nice_reasoning = "No preferred skills specified in job posting."

        # Map citations for nice-to-have skills
        nice_citations = []
        if nice_req_names and 'match_res' in locals():
            nice_citations = [
                {
                    "required_skill": m.required_skill,
                    "matched_candidate_skill": m.matched_candidate_skill,
                    "evidence_sentence": m.evidence_sentence,
                    "char_start": m.char_start,
                    "char_end": m.char_end,
                }
                for m in match_res.semantic_matches
                if m.evidence_sentence
            ]

        nice_score = ComponentScore(
            weight_percentage=W["nice_to_have"],
            raw_score=round(nice_raw, 1),
            weighted_score=round(nice_raw * w_nice, 2),
            reasoning=nice_reasoning,
            citations=nice_citations,
        )

        # ─── 4. Career Stability Score (10%) ───────────────────────────────────
        work_exp = parsed_resume.get("work_experience", [])
        if work_exp:
            total_jobs = len(work_exp)
            avg_months = sum(w.get("duration_months") or 24 for w in work_exp) / total_jobs
            if avg_months >= 30:
                stab_raw = 100.0
                stab_reasoning = f"Excellent career stability — avg tenure of {round(avg_months / 12, 1)} years across {total_jobs} role(s)."
            elif avg_months >= 18:
                stab_raw = 85.0
                stab_reasoning = f"Good career stability — avg tenure of {round(avg_months / 12, 1)} years per role."
            elif avg_months >= 12:
                stab_raw = 65.0
                stab_reasoning = f"Moderate career stability — avg tenure of {round(avg_months / 12, 1)} years per role."
            else:
                stab_raw = 40.0
                stab_reasoning = f"Frequent role changes detected — avg tenure of {round(avg_months / 12, 1)} years per role."
        else:
            stab_raw = 70.0
            stab_reasoning = "Work experience timeline not fully parsed."

        stab_score = ComponentScore(
            weight_percentage=W["career_stability"],
            raw_score=round(stab_raw, 1),
            weighted_score=round(stab_raw * w_stab, 2),
            reasoning=stab_reasoning,
        )

        # ─── 5. Industry Domain Match Score (8%) ───────────────────────────────
        # Compare candidate's industry domains and company background against job context
        cand_industries = parsed_resume.get("industry_domains", [])
        job_raw_desc = (job.raw_description or "").lower()
        job_title = (job.title or "").lower()
        cand_companies = parsed_resume.get("companies", [])

        # Build a list of industry signals from the job
        job_industry_signals = []
        industry_keyword_map = {
            "fintech / banking": ["bank", "finance", "fintech", "trading", "investment", "insurance"],
            "healthcare / medtech": ["healthcare", "hospital", "medical", "pharma", "clinical", "ehr"],
            "saas / enterprise software": ["saas", "b2b", "platform", "software", "cloud"],
            "e-commerce / retail": ["e-commerce", "retail", "shopify", "marketplace"],
            "data & analytics": ["analytics", "bi", "data engineering", "intelligence"],
            "cybersecurity": ["security", "cybersecurity", "soc", "siem"],
            "hr tech / talent": ["hr", "recruitment", "talent", "workforce"],
            "supply chain / logistics": ["logistics", "supply chain", "warehouse"],
            "manufacturing / industrial": ["manufacturing", "industrial", "factory"],
        }

        for domain, signals in industry_keyword_map.items():
            if any(sig in job_raw_desc or sig in job_title for sig in signals):
                job_industry_signals.append(domain)

        if cand_industries and job_industry_signals:
            # Check overlap between candidate industries and job industries
            overlap = [ind for ind in cand_industries if any(
                j_ind.split("/")[0].strip().lower() in ind.lower() or
                ind.lower().split("/")[0].strip() in j_ind.lower()
                for j_ind in job_industry_signals
            )]
            if overlap:
                ind_raw = 100.0
                ind_reasoning = f"Strong industry match — candidate has domain experience in: {', '.join(overlap[:3])}."
            else:
                ind_raw = 60.0
                ind_reasoning = f"Candidate has experience in {', '.join(cand_industries[:2])} — may need domain ramp-up for this role."
        elif cand_companies:
            ind_raw = 80.0
            ind_reasoning = f"Candidate has professional tenure at: {', '.join(cand_companies[:3])}."
        else:
            ind_raw = 55.0
            ind_reasoning = "Industry domain background not clearly established from resume."

        ind_score = ComponentScore(
            weight_percentage=W["industry_match"],
            raw_score=round(ind_raw, 1),
            weighted_score=round(ind_raw * w_ind, 2),
            reasoning=ind_reasoning,
        )

        # ─── 6. Education Fit Score (5%) ───────────────────────────────────────
        education_list = parsed_resume.get("education", [])
        req_edu = (job.education_requirement or "").lower()

        if education_list:
            top_degree = education_list[0].get("degree", "").lower()
            field = education_list[0].get("field_of_study", "") or ""

            if "phd" in top_degree or "doctorate" in top_degree:
                degree_level = 4
            elif "master" in top_degree or "mba" in top_degree or "mtech" in top_degree:
                degree_level = 3
            elif "bachelor" in top_degree or "btech" in top_degree or "b.sc" in top_degree:
                degree_level = 2
            else:
                degree_level = 1

            if "phd" in req_edu:
                req_level = 4
            elif "master" in req_edu or "mba" in req_edu:
                req_level = 3
            elif "bachelor" in req_edu or "degree" in req_edu:
                req_level = 2
            else:
                req_level = 1

            if degree_level >= req_level:
                edu_raw = 100.0
                edu_reasoning = f"Education match: {education_list[0].get('degree')} in {field} — meets or exceeds requirement."
            else:
                edu_raw = 75.0
                edu_reasoning = f"Education: {education_list[0].get('degree')} — slightly below preferred requirement."
        else:
            edu_raw = 65.0
            edu_reasoning = "Education not explicitly listed — may rely on equivalent experience."

        edu_score = ComponentScore(
            weight_percentage=W["education"],
            raw_score=round(edu_raw, 1),
            weighted_score=round(edu_raw * w_edu, 2),
            reasoning=edu_reasoning,
        )

        # ─── 7. Certifications Score (4%) ──────────────────────────────────────
        certs = parsed_resume.get("certifications", [])
        job_desc_lower = (job.raw_description or "").lower()

        if certs:
            # Check if any cert is relevant to the job
            relevant_certs = [c for c in certs if c.get("name", "").lower()[:10] in job_desc_lower]
            if relevant_certs:
                cert_raw = 100.0
                cert_reasoning = f"Relevant certifications for this role: {', '.join(c.get('name', '') for c in relevant_certs[:2])}."
            else:
                cert_raw = 85.0
                cert_reasoning = f"Has {len(certs)} professional certification(s): {', '.join(c.get('name', '') for c in certs[:2])}."
        else:
            cert_raw = 60.0
            cert_reasoning = "No professional certifications listed."

        cert_score = ComponentScore(
            weight_percentage=W["certifications"],
            raw_score=round(cert_raw, 1),
            weighted_score=round(cert_raw * w_cert, 2),
            reasoning=cert_reasoning,
        )

        # ─── 8. Location Score (3%) ────────────────────────────────────────────
        cand_loc = (parsed_resume.get("location") or "").lower()
        job_loc = (job.location or "").lower()

        if job.is_remote:
            loc_raw = 100.0
            loc_reasoning = "Remote position — location is not a barrier."
        elif "remote" in cand_loc:
            loc_raw = 95.0
            loc_reasoning = "Candidate is open to remote work."
        elif job_loc and cand_loc:
            # Check city/country overlap
            job_loc_parts = set(job_loc.replace(",", " ").split())
            cand_loc_parts = set(cand_loc.replace(",", " ").split())
            if job_loc_parts & cand_loc_parts:
                loc_raw = 100.0
                loc_reasoning = f"Location match: {parsed_resume.get('location')}."
            else:
                loc_raw = 70.0
                loc_reasoning = f"Location mismatch: Job in '{job.location}', candidate in '{parsed_resume.get('location')}'. Relocation or hybrid arrangement may be needed."
        else:
            loc_raw = 80.0
            loc_reasoning = "Location details not fully specified — assumed flexible."

        loc_score = ComponentScore(
            weight_percentage=W["location"],
            raw_score=round(loc_raw, 1),
            weighted_score=round(loc_raw * w_loc, 2),
            reasoning=loc_reasoning,
        )

        # ─── Compute Overall Score ──────────────────────────────────────────────
        overall = (
            mand_score.weighted_score
            + exp_score.weighted_score
            + nice_score.weighted_score
            + stab_score.weighted_score
            + ind_score.weighted_score
            + edu_score.weighted_score
            + cert_score.weighted_score
            + loc_score.weighted_score
        )
        overall = round(min(overall, 100.0), 1)

        # Gate / Capping Rules to prevent score clustering for unqualified candidates
        if mandatory_req_names:
            if matched_count == 0:
                overall = min(overall, 38.0)
            elif (matched_count / len(mandatory_req_names)) < 0.3:
                overall = min(overall, 50.0)

        # Generate a rich match summary
        top_skills = cand_skills[:4]
        summary = (
            f"Overall AI match score: {overall}/100. "
            f"Mandatory skills alignment: {mand_raw:.0f}%. "
            f"Experience: {cand_exp_years} yrs (required: {req_min_exp}–{req_max_exp} yrs). "
            f"Top candidate skills: {', '.join(top_skills) if top_skills else 'Not specified'}. "
            f"{mand_reasoning}"
        )

        # Compute Confidence Score based on parsing completeness
        conf = 95.0
        if not cand_skills:
            conf -= 20.0
        if not work_exp:
            conf -= 20.0
        if not parsed_resume.get("education"):
            conf -= 10.0
        if not parsed_resume.get("location") and not job.is_remote:
            conf -= 10.0
        conf_score = max(30.0, min(conf, 100.0))

        # Compute Hiring Risk Alerts
        hiring_risks = []
        if work_exp:
            total_jobs = len(work_exp)
            avg_months = sum(w.get("duration_months") or 24 for w in work_exp) / total_jobs
            if avg_months < 15:
                hiring_risks.append(f"Frequent job hopping: average tenure is {round(avg_months/12, 1)} years cross {total_jobs} roles.")
        
        if req_min_exp > 0 and cand_exp_years < req_min_exp:
            hiring_risks.append(f"Experience gap: has {cand_exp_years} years, targets {req_min_exp} minimum.")
            
        if req_max_exp > 0 and cand_exp_years > req_max_exp:
            hiring_risks.append(f"Overqualified candidate: experience ({cand_exp_years} years) exceeds target range of {req_min_exp}–{req_max_exp} years.")

        if missing_skills_list:
            hiring_risks.append(f"Missing core framework skills: {', '.join(missing_skills_list)}")
            
        if not job.is_remote and loc_raw < 80.0:
            hiring_risks.append(f"Geographic mismatch: candidate resides in '{parsed_resume.get('location') or 'unknown'}' vs target local job office '{job.location}'.")
            
        if not hiring_risks:
            hiring_risks.append("No major risk flags detected.")

        return ScoreBreakdownResponse(
            overall_score=overall,
            mandatory_skills=mand_score,
            experience=exp_score,
            industry_match=ind_score,
            nice_to_have_skills=nice_score,
            career_stability=stab_score,
            education=edu_score,
            location=loc_score,
            certifications=cert_score,
            match_summary=summary,
            confidence_score=conf_score,
            risks=hiring_risks,
        )
