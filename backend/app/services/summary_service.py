import json
from typing import List, Optional
from loguru import logger
import openai

from app.core.config import settings
from app.models.job import Job
from app.models.resume import Resume
from app.prompts.candidate_summary import get_candidate_summary_prompt
from app.schemas.matching import SemanticMatchRequest
from app.schemas.summary import CandidateSummaryResponse, FitRecommendation
from app.services.semantic_matcher_service import SemanticMatcherService


class SummaryService:
    """AI Service for generating recruiter summaries, missing skill highlights, and mismatch warnings."""

    @staticmethod
    async def generate_summary(job: Job, resume: Resume, version: str = "v1") -> CandidateSummaryResponse:
        parsed_job = job.parsed_data or {}
        parsed_resume = resume.parsed_data or {}

        if settings.OPENAI_API_KEY:
            try:
                return await SummaryService._openai_summary(job, resume, version=version)
            except Exception as e:
                logger.error(f"OpenAI Candidate Summary failed: {str(e)}. Using fallback summary engine.")

        return await SummaryService._fallback_summary(job, resume)

    @staticmethod
    async def _openai_summary(job: Job, resume: Resume, version: str = "v1") -> CandidateSummaryResponse:
        system_prompt = get_candidate_summary_prompt(version=version)
        user_prompt = f"""
        Job Posting:
        Title: {job.title}
        Required Experience: {job.min_experience_years} - {job.max_experience_years} years
        Mandatory Skills: {json.dumps(job.parsed_data.get('mandatory_skills', []) if job.parsed_data else [])}
        Location: {job.location} (Remote: {job.is_remote})
        Salary Budget: {job.min_salary} - {job.max_salary} {job.salary_currency}

        Candidate Resume Details:
        Name: {resume.candidate.full_name}
        Total Experience: {resume.parsed_data.get('total_experience_years') if resume.parsed_data else 0} years
        Skills: {json.dumps(resume.parsed_data.get('skills', []) if resume.parsed_data else [])}
        Location: {resume.parsed_data.get('location') if resume.parsed_data else 'Unknown'}
        Raw Text Summary: {resume.raw_text[:1500] if resume.raw_text else ''}
        """

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw_json = response.choices[0].message.content
        parsed_dict = json.loads(raw_json)
        return CandidateSummaryResponse(**parsed_dict)

    @staticmethod
    async def _fallback_summary(job: Job, resume: Resume) -> CandidateSummaryResponse:
        parsed_job = job.parsed_data or {}
        parsed_resume = resume.parsed_data or {}

        cand_exp = float(parsed_resume.get("total_experience_years") or 0.0)
        req_min_exp = float(job.min_experience_years or 0.0)

        mand_skills = [s.get("name", s) if isinstance(s, dict) else s for s in parsed_job.get("mandatory_skills", [])]
        cand_skills = [s.get("name") for s in parsed_resume.get("skills", []) if s.get("name")]

        missing_skills: List[str] = []
        if mand_skills:
            match_req = SemanticMatchRequest(
                required_skills=mand_skills,
                candidate_skills=cand_skills,
                candidate_experience_text=resume.raw_text,
            )
            match_res = await SemanticMatcherService.match_skills(match_req)
            missing_skills = [m.required_skill for m in match_res.semantic_matches if m.match_type.value == "MISSING"]

        # Weak Experience Warning
        weak_exp_warn = None
        if cand_exp < req_min_exp and req_min_exp > 0:
            weak_exp_warn = f"Experience gap: Candidate has {cand_exp} years vs {req_min_exp} years required."

        # Location Mismatch Warning
        loc_warn = None
        cand_loc = (parsed_resume.get("location") or "").lower()
        job_loc = (job.location or "").lower()
        if not job.is_remote and job_loc and cand_loc and job_loc not in cand_loc:
            loc_warn = f"Location mismatch: Job is in '{job.location}' but candidate is located in '{parsed_resume.get('location')}'."

        # Fit Recommendation
        if not missing_skills and cand_exp >= req_min_exp:
            fit = FitRecommendation.STRONG_FIT
        elif len(missing_skills) <= 1:
            fit = FitRecommendation.MODERATE_FIT
        else:
            fit = FitRecommendation.WEAK_FIT

        missing_str = ", ".join(missing_skills)
        exec_summary = (
            f"{cand_exp:.1f} years of professional experience with expertise in {', '.join(cand_skills[:4]) if cand_skills else 'relevant domains'}. "
            f"{'Strong alignment with job requirements.' if fit == FitRecommendation.STRONG_FIT else 'Good potential with a few skill/experience gaps.'} "
            f"{f'Missing: {len(missing_skills)} key skill(s) ({missing_str}).' if missing_skills else 'All mandatory skills present.'}"
        )

        return CandidateSummaryResponse(
            executive_summary=exec_summary,
            key_strengths=[f"Strong background in {s}" for s in cand_skills[:3]] or ["Proven domain experience"],
            missing_mandatory_skills=missing_skills,
            weak_experience_warning=weak_exp_warn,
            salary_mismatch_warning=None,
            location_mismatch_warning=loc_warn,
            fit_recommendation=fit,
        )
