import json
import re
from typing import Any, Dict, List
from loguru import logger
import openai

from app.core.config import settings
from app.prompts.jd_parser import get_jd_parser_prompt
from app.schemas.job import ExtractedSkill, JobStructuredExtract


class JDParserService:
    """Service for parsing raw Job Description text into structured JSON using AI LLMs."""

    @staticmethod
    async def parse_jd_text(raw_text: str, version: str = "v1") -> JobStructuredExtract:
        """Parse JD text via OpenAI GPT or rule-based fallback if API key is not present."""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not configured. Using Heuristic AI Rule-Engine for JD parsing.")
            return JDParserService._fallback_parse(raw_text)

        system_prompt = get_jd_parser_prompt(version=version)
        user_prompt = f"Analyze the following Job Description and return structured JSON:\n\n{raw_text}"

        try:
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
            return JobStructuredExtract(**parsed_dict)
        except Exception as e:
            logger.error(f"Failed to parse JD with OpenAI API: {str(e)}. Falling back to heuristic engine.")
            return JDParserService._fallback_parse(raw_text)

    @staticmethod
    def _fallback_parse(raw_text: str) -> JobStructuredExtract:
        """Heuristic rule engine for extracting structured data from raw JD when LLM is unavailable."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        first_line = lines[0] if lines else "Software Engineer"

        # Experience extraction regex (e.g. "5+ years", "3-5 years", "minimum 4 years")
        exp_match = re.search(r"(\d+)\s*[-to]*\s*(\d*)\s*\+?\s*years", raw_text, re.IGNORECASE)
        min_exp, max_exp = None, None
        if exp_match:
            min_exp = float(exp_match.group(1))
            if exp_match.group(2):
                max_exp = float(exp_match.group(2))

        # Extract Skills heuristic matching
        common_skills = [
            ("Python", "Programming Language"),
            ("FastAPI", "Web Framework"),
            ("React", "Frontend"),
            ("TypeScript", "Programming Language"),
            ("SQL", "Database"),
            ("PostgreSQL", "Database"),
            ("Docker", "DevOps"),
            ("AWS", "Cloud"),
            ("Power BI", "Data Analytics"),
            ("Machine Learning", "AI"),
            ("Git", "Tools"),
            ("REST API", "Architecture"),
        ]

        mandatory_skills: List[ExtractedSkill] = []
        good_to_have_skills: List[ExtractedSkill] = []

        text_lower = raw_text.lower()
        for name, category in common_skills:
            if name.lower() in text_lower:
                if len(mandatory_skills) < 4:
                    mandatory_skills.append(ExtractedSkill(name=name, category=category, synonyms=[]))
                else:
                    good_to_have_skills.append(ExtractedSkill(name=name, category=category, synonyms=[]))

        # Remote check
        is_remote = "remote" in text_lower or "work from home" in text_lower

        return JobStructuredExtract(
            role=first_line[:100] if len(first_line) < 100 else "Job Role",
            department="Engineering",
            min_experience_years=min_exp or 3.0,
            max_experience_years=max_exp or 6.0,
            mandatory_skills=mandatory_skills if mandatory_skills else [
                ExtractedSkill(name="Software Engineering", category="General", synonyms=[])
            ],
            good_to_have_skills=good_to_have_skills,
            education_requirement="Bachelor's Degree in Computer Science or related field",
            location="Remote" if is_remote else "San Francisco, CA",
            is_remote=is_remote,
            min_salary=80000.0,
            max_salary=140000.0,
            salary_currency="USD",
            responsibilities=[line for line in lines if len(line) > 30][:5],
        )
