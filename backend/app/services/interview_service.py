import json
from typing import List
from loguru import logger
import openai

from app.core.config import settings
from app.models.job import Job
from app.models.resume import Resume
from app.prompts.interview_questions import get_interview_questions_prompt
from app.schemas.copilot import (
    InterviewQuestionItem,
    PersonalizedInterviewQuestionsResponse,
    QuestionCategory,
)


class InterviewService:
    """AI Service for generating personalized, candidate-specific interview questions."""

    @staticmethod
    async def generate_questions(
        job: Job, resume: Resume, version: str = "v1"
    ) -> PersonalizedInterviewQuestionsResponse:
        if settings.OPENAI_API_KEY:
            try:
                return await InterviewService._openai_questions(job, resume, version=version)
            except Exception as e:
                logger.error(f"OpenAI Interview Question generation failed: {str(e)}. Using fallback questions generator.")

        return InterviewService._fallback_questions(job, resume)

    @staticmethod
    async def _openai_questions(
        job: Job, resume: Resume, version: str = "v1"
    ) -> PersonalizedInterviewQuestionsResponse:
        system_prompt = get_interview_questions_prompt(version=version)
        user_prompt = f"""
        Target Job Posting:
        Title: {job.title}
        Requirements: {job.raw_description[:1000]}

        Candidate Profile & Resume Claims:
        Name: {resume.candidate.full_name}
        Work Experience: {json.dumps(resume.parsed_data.get('work_experience', []) if resume.parsed_data else [])}
        Projects: {json.dumps(resume.parsed_data.get('projects', []) if resume.parsed_data else [])}
        Skills: {json.dumps(resume.parsed_data.get('skills', []) if resume.parsed_data else [])}
        Raw Resume: {resume.raw_text[:1500] if resume.raw_text else ''}
        """

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        raw_json = response.choices[0].message.content
        parsed_dict = json.loads(raw_json)
        questions = [InterviewQuestionItem(**q) for q in parsed_dict.get("questions", [])]

        return PersonalizedInterviewQuestionsResponse(
            candidate_id=str(resume.candidate_id),
            job_id=str(job.id),
            questions=questions,
        )

    @staticmethod
    def _fallback_questions(
        job: Job, resume: Resume
    ) -> PersonalizedInterviewQuestionsResponse:
        parsed_resume = resume.parsed_data or {}
        cand_name = resume.candidate.full_name
        skills = [s.get("name") for s in parsed_resume.get("skills", [])][:3]
        work_exp = parsed_resume.get("work_experience", [])
        last_comp = work_exp[0].get("company") if work_exp else "your previous company"
        last_role = work_exp[0].get("role") if work_exp else "your previous role"

        questions = [
            InterviewQuestionItem(
                category=QuestionCategory.RESUME_DEEP_DIVE,
                question=f"At {last_comp}, as a {last_role}, can you walk us through the technical architecture of your primary project?",
                rationale=f"Verifies claims from candidate's most recent position at {last_comp}.",
                expected_answer_signal="Deep technical clarity on system design, trade-offs, and personal contribution.",
            ),
            InterviewQuestionItem(
                category=QuestionCategory.TECHNICAL,
                question=f"You listed expertise in {', '.join(skills) if skills else 'core technologies'}. Can you describe a complex production bug you solved using these tools?",
                rationale=f"Evaluates hands-on problem solving with claimed primary skills.",
                expected_answer_signal="Clear debugging methodology, root cause isolation, and prevention strategy.",
            ),
            InterviewQuestionItem(
                category=QuestionCategory.BEHAVIORAL,
                question=f"Describe a situation when project requirements shifted mid-sprint for {job.title} initiatives. How did you realign engineering priorities?",
                rationale="Assesses adaptability and stakeholder communication.",
                expected_answer_signal="Structured prioritization, proactive communication, and zero panic.",
            ),
            InterviewQuestionItem(
                category=QuestionCategory.CLAIM_VERIFICATION,
                question="Can you quantify the exact performance or business impact of your deliverables in your recent projects?",
                rationale="Validates resume metric claims against actual project ownership.",
                expected_answer_signal="Specific metrics (e.g. latency reduced by X%, revenue increased by Y%).",
            ),
        ]

        return PersonalizedInterviewQuestionsResponse(
            candidate_id=str(resume.candidate_id),
            job_id=str(job.id),
            questions=questions,
        )
