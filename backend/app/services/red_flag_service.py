import json
from typing import List
from loguru import logger
import openai

from app.core.config import settings
from app.models.job import Job
from app.models.resume import Resume
from app.prompts.red_flag_detector import get_red_flag_detector_prompt
from app.schemas.copilot import (
    FlagSeverity,
    RedFlagAnalysisResponse,
    RedFlagItem,
    RedFlagType,
)


class RedFlagService:
    """Forensic AI Service for detecting timeline anomalies, employment gaps, fake experience indicators, and red flags."""

    @staticmethod
    async def analyze_red_flags(
        job: Job, resume: Resume, version: str = "v1"
    ) -> RedFlagAnalysisResponse:
        if settings.OPENAI_API_KEY:
            try:
                return await RedFlagService._openai_analysis(job, resume, version=version)
            except Exception as e:
                logger.error(f"OpenAI Red Flag Analysis failed: {str(e)}. Using rule-based anomaly detector.")

        return RedFlagService._heuristic_analysis(job, resume)

    @staticmethod
    async def _openai_analysis(
        job: Job, resume: Resume, version: str = "v1"
    ) -> RedFlagAnalysisResponse:
        system_prompt = get_red_flag_detector_prompt(version=version)
        user_prompt = f"""
        Job Requirement Context:
        Title: {job.title}
        Min Experience: {job.min_experience_years} years
        Raw Description: {job.raw_description[:1000]}

        Candidate Resume Data:
        Name: {resume.candidate.full_name}
        Work History: {json.dumps(resume.parsed_data.get('work_experience', []) if resume.parsed_data else [])}
        Education: {json.dumps(resume.parsed_data.get('education', []) if resume.parsed_data else [])}
        Skills: {json.dumps(resume.parsed_data.get('skills', []) if resume.parsed_data else [])}
        Raw Text: {resume.raw_text[:1500] if resume.raw_text else ''}
        """

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        raw_json = response.choices[0].message.content
        parsed_dict = json.loads(raw_json)

        flags = [RedFlagItem(**f) for f in parsed_dict.get("red_flags", [])]
        risk_score = float(parsed_dict.get("risk_score", 0.0))
        has_critical = any(f.severity == FlagSeverity.HIGH for f in flags)

        return RedFlagAnalysisResponse(
            candidate_id=str(resume.candidate_id),
            job_id=str(job.id),
            risk_score=round(risk_score, 1),
            has_critical_flags=has_critical,
            red_flags=flags,
        )

    @staticmethod
    def _heuristic_analysis(job: Job, resume: Resume) -> RedFlagAnalysisResponse:
        parsed_resume = resume.parsed_data or {}
        work_exp = parsed_resume.get("work_experience", [])
        education = parsed_resume.get("education", [])
        cand_exp = float(parsed_resume.get("total_experience_years") or 0.0)
        req_min = float(job.min_experience_years or 0.0)

        flags: List[RedFlagItem] = []

        # 1. Underqualified Check
        if cand_exp < (req_min * 0.5) and req_min >= 3.0:
            flags.append(
                RedFlagItem(
                    flag_type=RedFlagType.UNDERQUALIFIED,
                    severity=FlagSeverity.HIGH,
                    description=f"Significant experience gap for required role.",
                    evidence=f"Candidate has {cand_exp} yrs vs {req_min} yrs required by job.",
                )
            )

        # 2. Overqualified Check
        if cand_exp > (req_min + 7.0) and req_min > 0:
            flags.append(
                RedFlagItem(
                    flag_type=RedFlagType.OVERQUALIFIED,
                    severity=FlagSeverity.LOW,
                    description="Candidate experience level significantly exceeds job requirements.",
                    evidence=f"Candidate has {cand_exp} yrs vs {req_min} yrs target level.",
                )
            )

        # 3. Job Hopping Check (average tenure < 12 months)
        if len(work_exp) >= 3:
            durations = [w.get("duration_months") or 12 for w in work_exp]
            avg_months = sum(durations) / len(durations)
            if avg_months < 12:
                flags.append(
                    RedFlagItem(
                        flag_type=RedFlagType.JOB_HOPPING,
                        severity=FlagSeverity.MEDIUM,
                        description="Frequent job changes with short duration per role.",
                        evidence=f"Average employment tenure is {round(avg_months, 1)} months across {len(work_exp)} positions.",
                    )
                )

        # 4. Missing Education Credentials
        if not education and job.education_requirement:
            flags.append(
                RedFlagItem(
                    flag_type=RedFlagType.MISSING_EDUCATION,
                    severity=FlagSeverity.LOW,
                    description="Education details not explicitly specified on resume.",
                    evidence=f"Job requires '{job.education_requirement}' but no education degree listed.",
                )
            )

        risk_score = 0.0
        if any(f.severity == FlagSeverity.HIGH for f in flags):
            risk_score = 65.0
        elif any(f.severity == FlagSeverity.MEDIUM for f in flags):
            risk_score = 35.0
        elif flags:
            risk_score = 15.0

        return RedFlagAnalysisResponse(
            candidate_id=str(resume.candidate_id),
            job_id=str(job.id),
            risk_score=risk_score,
            has_critical_flags=any(f.severity == FlagSeverity.HIGH for f in flags),
            red_flags=flags,
        )
