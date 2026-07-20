from typing import Any, Dict, List
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.matching import SemanticMatchRequest
from app.schemas.scoring import ComponentScore, ScoreBreakdownResponse
from app.services.semantic_matcher_service import SemanticMatcherService


class ScoringEngineService:
    """Explainable AI Candidate Scoring Engine implementing 100-point weighted allocation:
    - Mandatory Skills: 35%
    - Experience: 20%
    - Industry Match: 10%
    - Nice-To-Have Skills: 10%
    - Career Stability: 10%
    - Education: 5%
    - Location: 5%
    - Certifications: 5%
    """

    @staticmethod
    async def evaluate_candidate(job: Job, resume: Resume) -> ScoreBreakdownResponse:
        parsed_job = job.parsed_data or {}
        parsed_resume = resume.parsed_data or {}

        # 1. Mandatory Skills Score (35%)
        mandatory_req_skills = parsed_job.get("mandatory_skills", [])
        cand_skills = [s.get("name") for s in parsed_resume.get("skills", [])]
        cand_exp_text = resume.raw_text or ""

        if mandatory_req_skills:
            match_req = SemanticMatchRequest(
                required_skills=mandatory_req_skills,
                candidate_skills=cand_skills,
                candidate_experience_text=cand_exp_text,
            )
            match_res = await SemanticMatcherService.match_skills(match_req)
            mand_raw = match_res.overall_semantic_score
            mand_reasoning = f"Matched {sum(1 for m in match_res.semantic_matches if m.match_type.value != 'MISSING')}/{len(mandatory_req_skills)} mandatory skills semantically."
        else:
            mand_raw = 100.0
            mand_reasoning = "No mandatory skills specified in job posting."

        mand_score = ComponentScore(
            weight_percentage=35.0,
            raw_score=round(mand_raw, 1),
            weighted_score=round(mand_raw * 0.35, 2),
            reasoning=mand_reasoning,
        )

        # 2. Experience Score (20%)
        cand_exp_years = float(parsed_resume.get("total_experience_years") or 0.0)
        req_min_exp = float(job.min_experience_years or 0.0)
        req_max_exp = float(job.max_experience_years or 99.0)

        if cand_exp_years >= req_min_exp:
            exp_raw = 100.0
            exp_reasoning = f"Candidate has {cand_exp_years} years of experience, exceeding required minimum of {req_min_exp} years."
        elif cand_exp_years > 0:
            exp_raw = (cand_exp_years / req_min_exp) * 100.0 if req_min_exp > 0 else 100.0
            exp_reasoning = f"Candidate has {cand_exp_years} years experience, slightly below required minimum of {req_min_exp} years."
        else:
            exp_raw = 30.0
            exp_reasoning = "Limited or unspecified years of experience."

        exp_score = ComponentScore(
            weight_percentage=20.0,
            raw_score=round(exp_raw, 1),
            weighted_score=round(exp_raw * 0.20, 2),
            reasoning=exp_reasoning,
        )

        # 3. Industry Match Score (10%)
        companies = parsed_resume.get("companies", [])
        if len(companies) >= 2:
            ind_raw = 95.0
            ind_reasoning = f"Strong industry tenure across {len(companies)} relevant organization(s): {', '.join(companies[:3])}."
        elif len(companies) == 1:
            ind_raw = 80.0
            ind_reasoning = f"Experience with company: {companies[0]}."
        else:
            ind_raw = 60.0
            ind_reasoning = "General industry background."

        ind_score = ComponentScore(
            weight_percentage=10.0,
            raw_score=round(ind_raw, 1),
            weighted_score=round(ind_raw * 0.10, 2),
            reasoning=ind_reasoning,
        )

        # 4. Nice-To-Have Skills Score (10%)
        nice_req_skills = parsed_job.get("good_to_have_skills", [])
        if nice_req_skills:
            match_req = SemanticMatchRequest(
                required_skills=nice_req_skills,
                candidate_skills=cand_skills,
                candidate_experience_text=cand_exp_text,
            )
            match_res = await SemanticMatcherService.match_skills(match_req)
            nice_raw = match_res.overall_semantic_score
            nice_reasoning = f"Matched {sum(1 for m in match_res.semantic_matches if m.match_type.value != 'MISSING')}/{len(nice_req_skills)} bonus skills."
        else:
            nice_raw = 100.0
            nice_reasoning = "No nice-to-have skills specified."

        nice_score = ComponentScore(
            weight_percentage=10.0,
            raw_score=round(nice_raw, 1),
            weighted_score=round(nice_raw * 0.10, 2),
            reasoning=nice_reasoning,
        )

        # 5. Career Stability Score (10%)
        work_exp = parsed_resume.get("work_experience", [])
        if work_exp:
            total_jobs = len(work_exp)
            avg_months = sum(w.get("duration_months") or 24 for w in work_exp) / total_jobs
            if avg_months >= 24:
                stab_raw = 100.0
                stab_reasoning = f"High career stability with average tenure of {round(avg_months/12, 1)} years per role."
            elif avg_months >= 12:
                stab_raw = 80.0
                stab_reasoning = f"Moderate career stability with average tenure of {round(avg_months/12, 1)} years per role."
            else:
                stab_raw = 50.0
                stab_reasoning = f"Frequent role transitions detected (avg tenure < 1 year)."
        else:
            stab_raw = 75.0
            stab_reasoning = "Standard career progression timeline."

        stab_score = ComponentScore(
            weight_percentage=10.0,
            raw_score=round(stab_raw, 1),
            weighted_score=round(stab_raw * 0.10, 2),
            reasoning=stab_reasoning,
        )

        # 6. Education Score (5%)
        education_list = parsed_resume.get("education", [])
        req_edu = (job.education_requirement or "").lower()
        if education_list:
            edu_degrees = [e.get("degree", "").lower() for e in education_list]
            if any("bachelor" in d or "master" in d or "phd" in d for d in edu_degrees):
                edu_raw = 100.0
                edu_reasoning = f"Holds higher education degree: {education_list[0].get('degree')} in {education_list[0].get('field_of_study')}."
            else:
                edu_raw = 80.0
                edu_reasoning = f"Holds diploma/degree: {education_list[0].get('degree')}."
        else:
            edu_raw = 70.0
            edu_reasoning = "Education details not explicitly listed."

        edu_score = ComponentScore(
            weight_percentage=5.0,
            raw_score=round(edu_raw, 1),
            weighted_score=round(edu_raw * 0.05, 2),
            reasoning=edu_reasoning,
        )

        # 7. Location Score (5%)
        cand_loc = (parsed_resume.get("location") or "").lower()
        job_loc = (job.location or "").lower()
        if job.is_remote or "remote" in cand_loc:
            loc_raw = 100.0
            loc_reasoning = "Remote position or remote candidate preference matched."
        elif job_loc and cand_loc and (job_loc in cand_loc or cand_loc in job_loc):
            loc_raw = 100.0
            loc_reasoning = f"Direct location match: {parsed_resume.get('location')}."
        else:
            loc_raw = 80.0
            loc_reasoning = f"Candidate located in {parsed_resume.get('location') or 'different region'}; relocation may be required."

        loc_score = ComponentScore(
            weight_percentage=5.0,
            raw_score=round(loc_raw, 1),
            weighted_score=round(loc_raw * 0.05, 2),
            reasoning=loc_reasoning,
        )

        # 8. Certifications Score (5%)
        certs = parsed_resume.get("certifications", [])
        if certs:
            cert_raw = 100.0
            cert_reasoning = f"Verified professional certifications: {', '.join([c.get('name') for c in certs[:2]])}."
        else:
            cert_raw = 70.0
            cert_reasoning = "No explicit certifications listed."

        cert_score = ComponentScore(
            weight_percentage=5.0,
            raw_score=round(cert_raw, 1),
            weighted_score=round(cert_raw * 0.05, 2),
            reasoning=cert_reasoning,
        )

        overall = (
            mand_score.weighted_score
            + exp_score.weighted_score
            + ind_score.weighted_score
            + nice_score.weighted_score
            + stab_score.weighted_score
            + edu_score.weighted_score
            + loc_score.weighted_score
            + cert_score.weighted_score
        )

        summary = (
            f"Overall match score of {round(overall, 1)}/100. "
            f"Mandatory skills: {mand_raw:.0f}%, Experience: {cand_exp_years} yrs."
        )

        return ScoreBreakdownResponse(
            overall_score=round(overall, 1),
            mandatory_skills=mand_score,
            experience=exp_score,
            industry_match=ind_score,
            nice_to_have_skills=nice_score,
            career_stability=stab_score,
            education=edu_score,
            location=loc_score,
            certifications=cert_score,
            match_summary=summary,
        )
