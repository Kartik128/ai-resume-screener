import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.job import Job
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.repositories.score_repository import ScoreRepository
from app.schemas.dashboard import CandidateComparisonColumn, ComparisonResponse
from app.services.red_flag_service import RedFlagService
from app.services.scoring_engine_service import ScoringEngineService


class ComparisonService:
    """Service for performing side-by-side multi-candidate matrix comparison."""

    @staticmethod
    async def compare_candidates(
        job_id: uuid.UUID,
        candidate_ids: List[uuid.UUID],
        company_id: uuid.UUID,
        db: AsyncSession,
    ) -> ComparisonResponse:
        job_repo = JobRepository(db)
        candidate_repo = CandidateRepository(db)
        score_repo = ScoreRepository(db)

        job = await job_repo.get_by_id(job_id, company_id)
        if not job:
            raise NotFoundException(resource="Job Posting", identifier=job_id)

        columns: List[CandidateComparisonColumn] = []
        mandatory_req_skills = (job.parsed_data or {}).get("mandatory_skills", [])

        for c_id in candidate_ids:
            candidate = await candidate_repo.get_by_id(c_id, company_id)
            if not candidate or not candidate.resumes:
                continue

            resume = candidate.resumes[0]
            score_ent = await score_repo.get_by_job_and_candidate(job.id, candidate.id)
            if not score_ent:
                breakdown = await ScoringEngineService.evaluate_candidate(job, resume)
                score_ent = await score_repo.save_or_update_score(
                    job_id=job.id,
                    candidate_id=candidate.id,
                    resume_id=resume.id,
                    breakdown=breakdown,
                )

            red_flag_res = await RedFlagService.analyze_red_flags(job, resume)
            cand_skills = [s.lower() for s in (candidate.raw_skills or [])]

            present = [s for s in mandatory_req_skills if s.lower() in cand_skills]
            missing = [s for s in mandatory_req_skills if s.lower() not in cand_skills]

            columns.append(
                CandidateComparisonColumn(
                    candidate_id=candidate.id,
                    full_name=candidate.full_name,
                    overall_score=score_ent.overall_score,
                    mandatory_skills_score=score_ent.mandatory_skills_score,
                    experience_score=score_ent.experience_score,
                    total_experience_years=candidate.total_experience_years or 0.0,
                    location=candidate.location,
                    mandatory_skills_present=present,
                    missing_skills=missing,
                    risk_score=red_flag_res.risk_score,
                )
            )

        if not columns:
            raise NotFoundException(resource="Candidates for comparison", identifier=str(candidate_ids))

        # Determine top recommendation
        top_cand = max(columns, key=lambda c: c.overall_score - (c.risk_score * 0.2))
        reasoning = (
            f"Candidate '{top_cand.full_name}' is recommended as top pick with overall score {top_cand.overall_score}/100, "
            f"{len(top_cand.mandatory_skills_present)}/{len(mandatory_req_skills)} mandatory skills present, and low risk score of {top_cand.risk_score}%."
        )

        return ComparisonResponse(
            job_id=job.id,
            job_title=job.title,
            recommended_top_candidate_id=top_cand.candidate_id,
            recommendation_reasoning=reasoning,
            columns=columns,
        )
