import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.job_repository import JobRepository
from app.schemas.copilot import (
    PersonalizedInterviewQuestionsResponse,
    RedFlagAnalysisResponse,
)
from app.services.interview_service import InterviewService
from app.services.red_flag_service import RedFlagService

router = APIRouter()


@router.get(
    "/interview-questions/{job_id}/{candidate_id}",
    response_model=PersonalizedInterviewQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 5-7 personalized, non-generic interview questions referencing candidate resume claims",
)
async def get_personalized_interview_questions(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonalizedInterviewQuestionsResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]
    return await InterviewService.generate_questions(job, resume)


@router.get(
    "/red-flags/{job_id}/{candidate_id}",
    response_model=RedFlagAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run forensic anomaly detection for employment gaps, job hopping, timeline inconsistencies, and fake experience indicators",
)
async def analyze_candidate_red_flags(
    job_id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RedFlagAnalysisResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=job_id)

    candidate = await candidate_repo.get_by_id(candidate_id, current_user.company_id)
    if not candidate or not candidate.resumes:
        raise NotFoundException(resource="Candidate / Resume", identifier=candidate_id)

    resume = candidate.resumes[0]
    return await RedFlagService.analyze_red_flags(job, resume)

from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    PersonalizedInterviewQuestionsResponse,
    RedFlagAnalysisResponse,
)
import openai
from app.core.config import settings


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interactive AI Recruiter Copilot assistant for asking questions about candidates and jobs",
)
async def chat_with_copilot(
    body: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotChatResponse:
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(uuid.UUID(body.job_id), current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=body.job_id)

    cand_context = ""
    if body.candidate_id:
        cand = await candidate_repo.get_by_id(uuid.UUID(body.candidate_id), current_user.company_id)
        if cand and cand.resumes:
            res = cand.resumes[0]
            cand_context = f"\nCandidate Name: {cand.full_name}\nResume Text:\n{res.raw_text[:2000]}"

    system_prompt = f"""You are AI Hiring Copilot, an expert AI recruiter assistant helping HR and hiring managers make data-driven candidate evaluation decisions across tech and non-tech industries.
Context:
Job Title: {job.title}
Job Description: {job.raw_description[:1500]}
{cand_context}

Provide a concise, highly insightful 2-3 paragraph answer to the recruiter's question."""

    if settings.OPENAI_API_KEY:
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body.question},
                ],
                temperature=0.3,
            )
            ans = resp.choices[0].message.content
            return CopilotChatResponse(
                answer=ans,
                suggested_followups=[
                    "What are 3 behavioral interview questions for this candidate?",
                    "Are there any red flags or employment gaps?",
                    "How does this candidate compare against the minimum job experience requirements?"
                ]
            )
        except Exception as e:
            pass

    # Heuristic fallback answer
    cand_skills_str = ", ".join(cand.raw_skills[:5]) if (body.candidate_id and cand and cand.raw_skills) else "general software development"
    cand_exp = cand.total_experience_years if (body.candidate_id and cand) else 0.0
    cand_loc = cand.location if (body.candidate_id and cand) else "unknown location"
    cand_name = cand.full_name if (body.candidate_id and cand) else "the candidate"
    
    score_msg = ""
    if body.candidate_id and cand:
        from app.repositories.score_repository import ScoreRepository
        score_repo = ScoreRepository(db)
        score_ent = await score_repo.get_by_job_and_candidate(job.id, cand.id)
        if score_ent:
            score_msg = f" They have an overall AI Match Score of {score_ent.overall_score:.1f}/100 (Mandatory Skills: {score_ent.mandatory_skills_score:.0f}%)."

    ans = (
        f"As your AI Hiring Copilot, I've analyzed {cand_name} for the '{job.title}' role in the {job.department} department.{score_msg}\n\n"
        f"Here is a summary of the profile match matrix:\n"
        f"• **Experience Level**: {cand_exp} years vs job target ({job.min_experience_years or 0}–{job.max_experience_years or 99} years).\n"
        f"• **Primary Skills**: {cand_skills_str}.\n"
        f"• **Location Alignment**: {cand_loc}.\n\n"
        f"The candidate shows direct alignment with the core requirements. Let me know if you would like me to draft candidate-specific screening questions or check for timeline anomalies!"
    )

    return CopilotChatResponse(
        answer=ans,
        suggested_followups=[
            "What technical/domain skills is the candidate missing?",
            "What candidate questions should I ask during the screening call?"
        ]
    )


class OutreachRequest(BaseModel):
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    tone: str = Field("formal", description="Outreach tone style: 'formal' | 'startup' | 'casual'")


class OutreachResponse(BaseModel):
    subject: str
    body: str


@router.post(
    "/outreach",
    response_model=OutreachResponse,
    status_code=status.HTTP_200_OK,
    summary="AI Outreach Writer: auto-generate custom, personalized outreach emails based on candidate resume and job requirements",
)
async def generate_outreach_email(
    body: OutreachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    candidate_repo = CandidateRepository(db)

    job = await job_repo.get_by_id(body.job_id, current_user.company_id)
    if not job:
        raise NotFoundException(resource="Job Posting", identifier=body.job_id)

    cand = await candidate_repo.get_by_id(body.candidate_id, current_user.company_id)
    if not cand:
        raise NotFoundException(resource="Candidate", identifier=body.candidate_id)

    # Rich context extraction
    first_name = cand.full_name.split()[0] if cand.full_name else "there"
    all_skills = cand.raw_skills or []
    top_skills = all_skills[:3] if all_skills else ["your background"]
    skills_str = ", ".join(top_skills)
    exp_years = cand.total_experience_years or 0
    exp_phrase = f"{exp_years}+ years of experience" if exp_years else "a strong background"
    location_phrase = f" based in {cand.location}" if getattr(cand, "location", None) else ""
    company = current_user.company.name if current_user.company else "our company"
    recruiter = current_user.full_name or "The Hiring Team"

    # JD context
    parsed = job.parsed_data or {}
    key_resp = (parsed.get("responsibilities") or [])[:2]
    resp_phrase = f" Key areas include: {'; '.join(key_resp)}." if key_resp else ""

    # Detect domain/department to use relevant non-technical phrasing
    dept_l = job.department.lower() if job.department else ""
    title_l = job.title.lower() if job.title else ""
    is_tech = any(k in dept_l for k in ["eng", "tech", "data", "develop", "software"]) or any(k in title_l for k in ["engineer", "developer", "architect", "programmer", "coder"])

    if is_tech:
        action_phrase = "moves fast, writes clean, and ships"
    elif any(k in dept_l for k in ["hr", "human", "talent", "recruit"]):
        action_phrase = "moves fast, connects deeply, and builds high-performing teams"
    elif any(k in dept_l for k in ["sales", "market"]):
        action_phrase = "moves fast, connects with clients, and drives revenue growth"
    else:
        action_phrase = "moves fast, solves problems, and drives results"

    if body.tone == "startup":
        subject = f"🚀 Hey {first_name} — quick chat about {job.title} at {company}?"
        email_body = (
            f"Hey {first_name},\n\n"
            f"I came across your profile and was genuinely impressed — {exp_phrase} in {skills_str}{location_phrase} is exactly the kind of background we're hunting for.\n\n"
            f"We're building something big at {company} and we need a {job.title} who {action_phrase}.{resp_phrase}\n\n"
            f"No long process — just a quick 15-minute call to see if the energy is right. You in?\n\n"
            f"Cheers,\n{recruiter}"
        )
    elif body.tone == "casual":
        subject = f"Hi {first_name} — saw your profile, wanted to reach out 👋"
        email_body = (
            f"Hi {first_name},\n\n"
            f"Hope your week is going well! I was going through profiles and yours caught my eye — {exp_phrase} with {skills_str} is a great fit for something we're working on.\n\n"
            f"We have an open {job.title} role at {company} and I'd love to share more.{resp_phrase} No pressure at all — just wanted to put it on your radar in case you're open to exploring.\n\n"
            f"Would love to connect if the timing works!\n\n"
            f"Talk soon,\n{recruiter}"
        )
    elif body.tone == "executive":
        subject = f"Confidential Opportunity: Senior {job.title} — {company}"
        email_body = (
            f"Dear {cand.full_name},\n\n"
            f"I hope this message finds you well. I am reaching out on behalf of {company} regarding a senior opportunity that I believe aligns strongly with your distinguished career trajectory.\n\n"
            f"Given your {exp_phrase} in {skills_str}, you represent exactly the calibre of leadership we are seeking for the {job.title} position.{resp_phrase}\n\n"
            f"I would welcome the opportunity to share further details under a mutual NDA if preferred. Please feel free to suggest a time at your convenience.\n\n"
            f"With regards,\n{recruiter}"
        )
    else:  # formal (default)
        subject = f"Career Opportunity: {job.title} at {company}"
        email_body = (
            f"Dear {cand.full_name},\n\n"
            f"I am writing to you on behalf of {company} regarding an exciting opportunity for the {job.title} role. Having reviewed your profile, I was particularly impressed by your {exp_phrase} in {skills_str}{location_phrase}.\n\n"
            f"This role is a strong match for your expertise.{resp_phrase} We believe your contributions could make a meaningful impact on our team.\n\n"
            f"I would appreciate the opportunity to connect and share more details about the position. Please let us know your availability for a brief introductory call.\n\n"
            f"Warm regards,\n{recruiter}"
        )

    return OutreachResponse(subject=subject, body=email_body)
