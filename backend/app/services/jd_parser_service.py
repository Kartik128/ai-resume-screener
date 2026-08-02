import json
import re
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import openai

from app.core.config import settings
from app.prompts.jd_parser import get_jd_parser_prompt
from app.schemas.job import ExtractedSkill, JobStructuredExtract
from app.services.skill_taxonomy_service import SkillTaxonomyService


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
    def _extract_role_title(raw_text: str) -> str:
        """Extract the job role title from a JD text using multiple strategies."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        # Strategy 1: Explicit label patterns — "Job Title: ...", "Position: ..."
        title_patterns = [
            r"(?:job\s+title|position|role|title)\s*[:\-]\s*(.{5,80})",
            r"(?:we are hiring|we're hiring|hiring(?:\s+a)?|seeking(?:\s+a)?)\s+(?:an?\s+)?(.{5,80})",
            r"(?:opening for|vacancy for|job opening)[:\-]?\s*(.{5,80})",
        ]
        for pat in title_patterns:
            match = re.search(pat, raw_text, re.IGNORECASE)
            if match:
                title = match.group(1).strip().split("\n")[0].split(".")[0].strip()
                if 3 < len(title) < 100:
                    return title

        # Strategy 2: Dash/em-dash/en-dash separated title line (first 5 lines)
        # e.g. "Senior PM – Payments & FinTech Platform" or "Data Engineer | Healthcare"
        # Support ASCII hyphen, en-dash (–), em-dash (—), pipe (|)
        dash_pattern = re.compile(
            r"^(.{5,60}?)\s*[\u2013\u2014\-\|]+\s*.{3,}$"
        )
        # Lines that look like company metadata (not job titles)
        metadata_line_pattern = re.compile(
            r"(?:company\s*:|location\s*:|salary\s*:|department\s*:|remote\s*:|"
            r"email\s*:|phone\s*:|linkedin\s*:|\$[\d,]+|@|\bllc\b|\binc\b|\bltd\b)",
            re.IGNORECASE,
        )
        for line in lines[:6]:
            if metadata_line_pattern.search(line):
                continue
            m = dash_pattern.match(line.strip())
            if m:
                return line.strip()  # Return full title "Role – Qualifier"

        # Strategy 3: First short non-metadata line that looks like a title
        company_desc_pattern = re.compile(
            r"(?:builds|provides|delivers|offers|develops|is a|is an|is the|"
            r"\bllc\b|\binc\b|\bltd\b|\bprocessing\b|\bpowered\b)",
            re.IGNORECASE,
        )
        skip_starts = {"about", "company", "description", "overview", "summary",
                       "responsibilities", "we are", "we're", "location", "salary",
                       "department", "requirements", "qualifications", "the role",
                       "note:", "please ", "equal "}

        for line in lines[:12]:
            lower = line.lower()
            if (5 < len(line) < 80 and
                    not line.endswith(":") and
                    not re.match(r'^[\-•\*\d\$\+]', line) and
                    not any(lower.startswith(s) for s in skip_starts) and
                    not metadata_line_pattern.search(line) and
                    not company_desc_pattern.search(line) and
                    not re.search(r'\s[a-z]{3,}\s[a-z]{3,}', line)):  # not a sentence
                return line

        # Strategy 4: Scan the entire text for a known job-title keyword combo
        # (Principal/Senior/Lead + Engineer/Manager/Analyst/Director/Scientist/Developer)
        title_kw_pattern = re.compile(
            r"\b(?:Principal|Senior|Lead|Staff|Head of|Director of|VP of|Chief)?\s*"
            r"(?:Data Engineer|Software Engineer|Product Manager|Data Scientist|"
            r"Data Analyst|Machine Learning|DevOps Engineer|Full Stack|Backend|Frontend|"
            r"Solutions Architect|Business Analyst|Project Manager|Scrum Master|"
            r"Technical Lead|Engineering Manager|Product Designer|UX Designer|"
            r"Marketing Manager|Sales Manager|HR Manager|Finance Manager|"
            r"Clinical Informatics|Biomedical|Bioinformatics)\b",
            re.IGNORECASE,
        )
        for line in lines[:20]:
            m = title_kw_pattern.search(line)
            if m and len(line) < 100:
                return line.strip()

        return lines[0][:80] if lines else "Job Role"



    @staticmethod
    def _extract_department(raw_text: str) -> str:
        """Try to extract the department from the JD."""
        dept_pattern = r"(?:department|team|division|group)\s*[:\-]\s*(.+)"
        match = re.search(dept_pattern, raw_text, re.IGNORECASE)
        if match:
            dept = match.group(1).strip().split("\n")[0].strip()
            if 2 < len(dept) < 80:
                return dept

        # Infer department from role keywords
        text_lower = raw_text.lower()
        dept_keywords = {
            "engineering": ["software engineer", "backend", "frontend", "fullstack", "devops", "sre", "developer"],
            "data & analytics": ["data scientist", "data analyst", "data engineer", "business intelligence", "ml engineer"],
            "product management": ["product manager", "product owner", "product lead"],
            "sales": ["sales", "account executive", "business development", "bdr", "sdr"],
            "marketing": ["marketing", "growth", "brand", "seo", "content"],
            "finance": ["finance", "accounting", "cfo", "controller", "auditor", "financial analyst"],
            "human resources": ["hr", "human resources", "recruiter", "talent acquisition", "payroll", "compensation", "benefits", "total rewards", "talent management"],
            "legal": ["legal", "counsel", "attorney", "paralegal", "compliance"],
            "operations": ["operations", "supply chain", "logistics", "warehouse"],
            "healthcare": ["nurse", "doctor", "physician", "therapist", "clinical"],
            "design": ["designer", "ux", "ui", "graphic", "visual design"],
            "customer success": ["customer success", "customer support", "account manager", "customer service"],
        }
        for dept, keywords in dept_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return dept.title()

        return "General"

    @staticmethod
    def _extract_experience(raw_text: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract min/max years of experience from the JD text."""
        patterns = [
            r"(\d+)\s*[-–to]+\s*(\d+)\s*\+?\s*years?",       # "3-5 years", "3 to 5 years"
            r"(\d+)\s*\+\s*years?",                             # "5+ years"
            r"minimum\s+(?:of\s+)?(\d+)\s*years?",             # "minimum of 3 years"
            r"at\s+least\s+(\d+)\s*years?",                    # "at least 4 years"
            r"(\d+)\s*years?\s+(?:of\s+)?experience",          # "5 years of experience"
        ]

        for pat in patterns:
            match = re.search(pat, raw_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:
                    return float(groups[0]), float(groups[1])
                elif groups[0]:
                    base = float(groups[0])
                    return base, base + 3

        return None, None

    @staticmethod
    def _extract_salary(raw_text: str) -> Tuple[Optional[float], Optional[float], str]:
        """Extract salary range and currency from the JD."""
        # Patterns like "$80,000 - $120,000", "80k-120k", "USD 80000 to 120000"
        patterns = [
            r"[\$£€₹¥]?\s*(\d[\d,]+k?)\s*[-–to]+\s*[\$£€₹¥]?\s*(\d[\d,]+k?)",
            r"(?:salary|compensation|pay)[:\s]+[\$£€₹¥]?\s*(\d[\d,]+k?)\s*[-–to]+\s*[\$£€₹¥]?\s*(\d[\d,]+k?)",
            r"(\d[\d,]+)\s*(?:per\s+(?:year|annum|pa))",
        ]

        currency_map = {"$": "USD", "£": "GBP", "€": "EUR", "₹": "INR", "¥": "JPY"}
        detected_currency = "USD"
        for sym, cur in currency_map.items():
            if sym in raw_text:
                detected_currency = cur
                break

        for pat in patterns:
            match = re.search(pat, raw_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    def parse_val(v: str) -> float:
                        v = v.replace(",", "").strip()
                        if v.lower().endswith("k"):
                            return float(v[:-1]) * 1000
                        return float(v)

                    min_sal = parse_val(groups[0])
                    max_sal = parse_val(groups[1]) if len(groups) > 1 and groups[1] else min_sal * 1.3
                    return min_sal, max_sal, detected_currency
                except Exception:
                    continue

        return None, None, "USD"

    @staticmethod
    def _extract_location(raw_text: str) -> Tuple[str, bool]:
        """Extract location and remote status from the JD."""
        text_lower = raw_text.lower()

        is_remote = any(phrase in text_lower for phrase in [
            "fully remote", "100% remote", "work from home", "wfh", "remote only",
            "remote-first", "remote position", "remote role", "work remotely"
        ])

        is_hybrid = "hybrid" in text_lower

        location_pattern = r"(?:location|based in|office(?:\s+location)?|headquarters?)\s*[:\-]\s*(.+)"
        match = re.search(location_pattern, raw_text, re.IGNORECASE)
        if match:
            loc = match.group(1).strip().split("\n")[0].split(",")[:2]
            return ", ".join(l.strip() for l in loc), is_remote

        # City/Country detection
        city_pattern = r"\b((?:New York|San Francisco|Los Angeles|Chicago|Austin|Seattle|Boston|London|Berlin|Amsterdam|Bangalore|Hyderabad|Mumbai|Delhi|Dubai|Singapore|Toronto|Sydney|Remote)(?:,\s*[A-Z]{2})?)\b"
        match = re.search(city_pattern, raw_text)
        if match:
            return match.group(1), is_remote

        if is_remote:
            return "Remote", True
        if is_hybrid:
            return "Hybrid", False

        return "Not Specified", False

    @staticmethod
    def _extract_education(raw_text: str) -> str:
        """Extract education requirements from the JD."""
        patterns = [
            r"(?:bachelor'?s?|b\.s\.?|b\.e\.?|be|btech|b\.tech)\s*(?:degree)?\s*(?:in\s+(.+?))?(?:[,;\n]|$)",
            r"(?:master'?s?|m\.s\.?|mba|m\.e\.?|mtech|m\.tech)\s*(?:degree)?\s*(?:in\s+(.+?))?(?:[,;\n]|$)",
            r"(?:phd|doctorate|doctoral)\s*(?:degree)?\s*(?:in\s+(.+?))?(?:[,;\n]|$)",
            r"(?:associate'?s?|a\.s\.?)\s*(?:degree)?\s*(?:in\s+(.+?))?(?:[,;\n]|$)",
            r"high school diploma",
            r"(?:degree|diploma|certification)\s*(?:in\s+(.+?))?(?:[,;\n]|$)",
        ]

        for pat in patterns:
            match = re.search(pat, raw_text, re.IGNORECASE)
            if match:
                full_match = match.group(0).strip()
                if len(full_match) > 3:
                    return full_match[:200].split("\n")[0].strip()

        return "Relevant degree or equivalent experience"

    @staticmethod
    def _extract_responsibilities(raw_text: str) -> List[str]:
        """Extract key responsibilities / job duties from the JD."""
        lines = raw_text.splitlines()
        responsibilities = []

        # Look for responsibility/duties section
        in_resp_section = False
        resp_section_headers = {
            "responsibilities", "what you'll do", "what you will do", "key duties",
            "your role", "duties", "day to day", "day-to-day", "role overview",
            "job duties", "role description"
        }
        end_section_headers = {
            "requirements", "qualifications", "must have", "required skills",
            "nice to have", "benefits", "about us", "about the company"
        }

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower().rstrip(":")

            if any(h in lower for h in resp_section_headers):
                in_resp_section = True
                continue

            if in_resp_section:
                if any(h in lower for h in end_section_headers):
                    break
                # Capture bullet-point lines or substantial sentences
                if re.match(r"^[\-\•\*\>✓►→]", stripped) or (len(stripped) > 30 and len(stripped) < 300):
                    clean = re.sub(r"^[\-\•\*\>✓►→]\s*", "", stripped)
                    if clean and len(clean) > 20:
                        responsibilities.append(clean)

        # Fallback: grab any bullet-point lines from the full text
        if not responsibilities:
            for line in lines:
                stripped = line.strip()
                if re.match(r"^[\-\•\*\>✓►→]", stripped) and len(stripped) > 30:
                    clean = re.sub(r"^[\-\•\*\>✓►→]\s*", "", stripped)
                    if clean and len(clean) > 20:
                        responsibilities.append(clean)
                if len(responsibilities) >= 10:
                    break

        return responsibilities[:10]

    @staticmethod
    def _fallback_parse(raw_text: str) -> JobStructuredExtract:
        """Heuristic NLP engine for extracting structured data from raw JD when LLM is unavailable."""
        # Extract all components
        role = JDParserService._extract_role_title(raw_text)
        department = JDParserService._extract_department(raw_text)
        min_exp, max_exp = JDParserService._extract_experience(raw_text)
        min_salary, max_salary, salary_currency = JDParserService._extract_salary(raw_text)
        location, is_remote = JDParserService._extract_location(raw_text)
        education = JDParserService._extract_education(raw_text)
        responsibilities = JDParserService._extract_responsibilities(raw_text)

        # Deep Skill Taxonomy & Keyword Extraction
        mand_raw, good_raw = SkillTaxonomyService.extract_skills_from_text(raw_text)

        mandatory_skills = [
            ExtractedSkill(name=s["name"], category=s["category"], synonyms=s.get("synonyms", []))
            for s in mand_raw
        ]
        good_to_have_skills = [
            ExtractedSkill(name=s["name"], category=s["category"], synonyms=s.get("synonyms", []))
            for s in good_raw
        ]

        logger.info(
            f"Fallback parser extracted: role='{role}', dept='{department}', "
            f"mandatory_skills={len(mandatory_skills)}, good_to_have={len(good_to_have_skills)}, "
            f"responsibilities={len(responsibilities)}"
        )

        return JobStructuredExtract(
            role=role,
            department=department,
            min_experience_years=min_exp if min_exp is not None else 0.0,
            max_experience_years=max_exp if max_exp is not None else 10.0,
            mandatory_skills=mandatory_skills if mandatory_skills else [
                ExtractedSkill(name="Domain Experience", category="General", synonyms=[])
            ],
            good_to_have_skills=good_to_have_skills,
            education_requirement=education,
            location=location,
            is_remote=is_remote,
            min_salary=min_salary,
            max_salary=max_salary,
            salary_currency=salary_currency,
            responsibilities=responsibilities,
        )
