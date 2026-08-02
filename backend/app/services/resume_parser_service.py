import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import openai

from app.core.config import settings
from app.prompts.resume_parser import get_resume_parser_prompt
from app.schemas.resume import (
    CertificationDTO,
    EducationDTO,
    ProjectDTO,
    ResumeStructuredExtract,
    SkillItemDTO,
    WorkExperienceDTO,
)
from app.services.skill_taxonomy_service import SkillTaxonomyService


class ResumeParserService:
    """AI Service for extracting comprehensive structured candidate profiles from raw resume text.
    Covers all resume sections: contact info, work experience, education, skills, projects,
    certifications, achievements, and industry context — for all industries.
    """

    @staticmethod
    def _clean_extracted_skills(skills: List[Any], raw_text: Optional[str] = None, candidate_name: Optional[str] = None) -> List[SkillItemDTO]:
        blacklist = {
            "professional experience", "work experience", "experience", "education", "skills",
            "summary", "objective", "contact", "profile", "achievements", "certifications",
            "projects", "publications", "languages", "references", "candidate", "resume", "cv",
            "job title", "location", "salary", "remote", "general", "expert", "senior", "junior",
            "lead", "manager", "director", "specialist"
        }
        
        # If candidate name parts are provided, blacklist them
        if candidate_name:
            for part in candidate_name.lower().split():
                if len(part) > 2:
                    blacklist.add(part)
                    
        # Check if candidate is HR/Talent Acquisition profile
        is_hr_profile = False
        if raw_text:
            text_lower = raw_text.lower()
            hr_keywords = {"recruiter", "talent acquisition", "human resources", "hr specialist", "hiring"}
            if any(kw in text_lower for kw in hr_keywords):
                is_hr_profile = True
                
        tech_blacklist = {
            "ci/cd", "c#", "java", "python", "kubernetes", "docker", "aws", "gcp", "azure", 
            "c++", "c", "javascript", "react", "node.js", "typescript", "git"
        }

        cleaned = []
        seen = set()
        for s in skills:
            name = s.name if hasattr(s, "name") else s.get("name")
            category = s.category if hasattr(s, "category") else s.get("category", "General")
            if not name or not name.strip():
                continue
            name_lower = name.strip().lower()
            
            # Prevent candidates' own name from becoming a skill
            if candidate_name and candidate_name.strip().lower() == name_lower:
                continue
                
            if name_lower in blacklist:
                continue
                
            if is_hr_profile and name_lower in tech_blacklist:
                continue
                
            if len(name_lower) < 2 or len(name_lower) > 50:
                continue
                
            if name_lower not in seen:
                seen.add(name_lower)
                if hasattr(s, "name"):
                    cleaned.append(s)
                else:
                    cleaned.append(SkillItemDTO(name=name.strip(), category=category))
        return cleaned

    @staticmethod
    async def parse_resume_text(raw_text: str, version: str = "v1") -> ResumeStructuredExtract:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. Using Heuristic Rule Engine for Resume Parsing.")
            return ResumeParserService._fallback_parse(raw_text)

        system_prompt = get_resume_parser_prompt(version=version)
        user_prompt = f"Analyze the following resume text and extract complete structured JSON:\n\n{raw_text}"

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
            
            # Clean skills list to remove headers and generic words
            if "skills" in parsed_dict:
                parsed_dict["skills"] = [
                    {"name": s.get("name", ""), "category": s.get("category", "General")}
                    for s in parsed_dict["skills"]
                ]
            
            extract = ResumeStructuredExtract(**parsed_dict)
            extract.skills = ResumeParserService._clean_extracted_skills(extract.skills, raw_text=raw_text, candidate_name=extract.name)
            return extract
        except Exception as e:
            logger.error(f"OpenAI Resume Parsing failed: {str(e)}. Falling back to heuristic engine.")
            return ResumeParserService._fallback_parse(raw_text)

    # ─────────────────────────────────────────────────────────────────────────────
    # HEURISTIC FALLBACK PARSER  (used when no OpenAI API key is configured)
    # ─────────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_contact(raw_text: str) -> Dict[str, Optional[str]]:
        """Extract name, email, phone, location, and social URLs from resume header."""
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        # Name: first non-empty line that isn't a label
        skip_labels = {"resume", "curriculum vitae", "cv", "profile", "contact"}
        name = "Candidate"
        for line in lines[:5]:
            if line.lower() not in skip_labels and len(line) > 2 and len(line) < 80:
                name = line
                break

        email_match = re.search(r"[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+", raw_text)
        email = email_match.group(0) if email_match else None

        phone_match = re.search(r"[\+\(]?\d[\d\s\-\.\(\)]{7,15}\d", raw_text)
        phone = phone_match.group(0).strip() if phone_match else None

        linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", raw_text, re.IGNORECASE)
        linkedin_url = f"https://{linkedin_match.group(0)}" if linkedin_match else None

        github_match = re.search(r"github\.com/[\w\-]+", raw_text, re.IGNORECASE)
        github_url = f"https://{github_match.group(0)}" if github_match else None

        portfolio_match = re.search(
            r"(?:portfolio|website|site|www)\s*[:\s]+?(https?://[\S]+|www\.[\S]+)",
            raw_text, re.IGNORECASE
        )
        portfolio_url = portfolio_match.group(1) if portfolio_match else None

        # Location: look for patterns like "City, State" or "City, Country"
        location_match = re.search(
            r"(?:location|based in|address|city|residing in)?\s*[:\-]?\s*"
            r"([A-Z][a-zA-Z\s]+,\s*(?:[A-Z]{2}|[A-Z][a-zA-Z\s]+))",
            raw_text
        )
        location = location_match.group(1).strip() if location_match else None

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
        }

    @staticmethod
    def _extract_summary(raw_text: str) -> Optional[str]:
        """Extract professional summary or objective from resume."""
        patterns = [
            r"(?:professional summary|summary|objective|profile|about me|career summary)[:\s]*\n([\s\S]{50,600}?)(?:\n\n|\n[A-Z])",
        ]
        for pat in patterns:
            match = re.search(pat, raw_text, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 20:
                    return summary[:600]

        # Fallback: return first substantive paragraph
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 80]
        if paragraphs:
            return paragraphs[0][:400]
        return None

    @staticmethod
    def _parse_date_to_months(date_str: str) -> Optional[int]:
        """Convert date string like '01/2021', '2021', 'Jan 2021' to months since epoch."""
        if not date_str:
            return None
        date_str = date_str.strip()
        if date_str.lower() in ("present", "current", "now", "ongoing"):
            now = datetime.now()
            return now.year * 12 + now.month

        formats = ["%m/%Y", "%Y", "%b %Y", "%B %Y", "%m-%Y", "%Y-%m"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.year * 12 + dt.month
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_work_experience(raw_text: str) -> Tuple[List[WorkExperienceDTO], List[str], float]:
        """Extract all work experience entries, company names, and total years."""
        # Find work experience section
        sections = re.split(
            r"\n(?:work experience|professional experience|employment history|experience|career history)\s*\n",
            raw_text, flags=re.IGNORECASE
        )

        if len(sections) < 2:
            # Try to find any section that contains date patterns (company entries)
            exp_section = raw_text
        else:
            # Take everything after the first match up to next major section
            exp_section = sections[1]
            end_pattern = re.compile(
                r"\n(?:education|skills|certifications|projects|achievements|publications|languages|references)\s*\n",
                re.IGNORECASE
            )
            end_match = end_pattern.search(exp_section)
            if end_match:
                exp_section = exp_section[:end_match.start()]

        # Parse individual job entries using date patterns as anchors
        # Pattern: "Company Name\nRole Title\nDate – Date"
        job_block_pattern = re.compile(
            r"^(.*?)\n(.*?)\n(.*?\d{4}.*?(?:–|-|to)\s*(?:Present|\d{4}|current).*?)\n?",
            re.MULTILINE | re.IGNORECASE
        )

        work_exp_entries: List[WorkExperienceDTO] = []
        companies: List[str] = []
        total_months = 0

        # Simpler approach: find lines with year ranges
        lines = exp_section.splitlines()
        current_entry: Optional[Dict] = None

        date_pattern = re.compile(
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|"
            r"July|August|September|October|November|December)?\s*"
            r"(\d{4})\s*[-–to]+\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|"
            r"July|August|September|October|November|December)?\s*"
            r"(\d{4}|present|current|ongoing|now)",
            re.IGNORECASE
        )
        simple_year_range = re.compile(r"(\d{4})\s*[-–to]+\s*(\d{4}|present|current)", re.IGNORECASE)

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            date_m = date_pattern.search(stripped) or simple_year_range.search(stripped)
            if date_m:
                # Save previous entry
                if current_entry:
                    entry = ResumeParserService._finalize_entry(current_entry)
                    if entry and entry.company:
                        work_exp_entries.append(entry)
                        if entry.company not in companies:
                            companies.append(entry.company)
                        if entry.duration_months:
                            total_months += entry.duration_months

                current_entry = {
                    "date_line": stripped,
                    "company": lines[i - 1].strip() if i > 0 else "",
                    "role": lines[i - 2].strip() if i > 1 else "",
                    "responsibilities": [],
                    "skills_used": [],
                }
            elif current_entry and stripped.startswith(("•", "-", "✓", "→", "*", "›")):
                cleaned = re.sub(r"^[•\-✓→\*›]\s*", "", stripped)
                if len(cleaned) > 15:
                    current_entry["responsibilities"].append(cleaned)

        # Save last entry
        if current_entry:
            entry = ResumeParserService._finalize_entry(current_entry)
            if entry and entry.company:
                work_exp_entries.append(entry)
                if entry.company not in companies:
                    companies.append(entry.company)
                if entry.duration_months:
                    total_months += entry.duration_months

        total_exp_years = round(total_months / 12, 1) if total_months > 0 else 0.0

        # Fallback: simple regex for explicit "X years" mentions
        if total_exp_years == 0:
            exp_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s*)?(?:experience|exp)", raw_text, re.IGNORECASE)
            if exp_match:
                total_exp_years = float(exp_match.group(1))

        return work_exp_entries, companies, total_exp_years

    @staticmethod
    def _finalize_entry(entry: Dict) -> Optional[WorkExperienceDTO]:
        """Convert a raw parsed entry dict into a WorkExperienceDTO."""
        company = entry.get("company", "").strip()
        role = entry.get("role", "").strip()
        date_line = entry.get("date_line", "")

        if not company or len(company) > 100:
            return None

        # Parse dates from date_line
        start_date, end_date, is_current, duration_months = ResumeParserService._parse_date_range(date_line)

        return WorkExperienceDTO(
            company=company,
            role=role or "Professional Role",
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            duration_months=duration_months,
            responsibilities=entry.get("responsibilities", [])[:8],
            skills_used=entry.get("skills_used", []),
        )

    @staticmethod
    def _parse_date_range(date_str: str) -> Tuple[Optional[str], str, bool, Optional[int]]:
        """Parse a date range string like '2019 - 2022' or 'Jan 2020 – Present'."""
        is_current = bool(re.search(r"present|current|ongoing|now", date_str, re.IGNORECASE))

        year_matches = re.findall(r"\d{4}", date_str)
        if not year_matches:
            return None, "Present" if is_current else "Unknown", is_current, None

        start_year = year_matches[0]
        end_year = year_matches[1] if len(year_matches) > 1 else (str(datetime.now().year) if is_current else start_year)

        start_months = int(start_year) * 12
        end_months = int(end_year) * 12 if not is_current else (datetime.now().year * 12 + datetime.now().month)
        duration = max(0, end_months - start_months)

        return start_year, "Present" if is_current else end_year, is_current, duration

    @staticmethod
    def _extract_education(raw_text: str) -> List[EducationDTO]:
        """Extract education entries from resume."""
        education_entries: List[EducationDTO] = []

        edu_keywords = ["bachelor", "master", "phd", "doctorate", "mba", "btech", "mtech", "be", "me",
                        "b.sc", "m.sc", "diploma", "associate", "high school", "secondary"]

        lines = raw_text.splitlines()
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in edu_keywords):
                # Extract degree and field
                degree_match = re.search(
                    r"(bachelor(?:'s)?|master(?:'s)?|phd|mba|b\.?tech|m\.?tech|b\.?sc|m\.?sc|diploma|doctorate|associate(?:'s)?)",
                    line, re.IGNORECASE
                )
                degree = degree_match.group(0).strip() if degree_match else "Degree"

                field_match = re.search(r"(?:of|in)\s+([A-Za-z\s,&]+?)(?:\s*,|\s*\(|\s*\d{4}|$)", line, re.IGNORECASE)
                field = field_match.group(1).strip() if field_match else None

                years = re.findall(r"\d{4}", " ".join(lines[max(0, i):i + 3]))
                start_year = years[0] if years else None
                end_year = years[1] if len(years) > 1 else None

                institution = ""
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and len(next_line) > 5 and not any(kw in next_line.lower() for kw in edu_keywords):
                        institution = next_line
                        break
                if not institution and i > 0:
                    institution = lines[i - 1].strip()

                education_entries.append(EducationDTO(
                    institution=institution[:100] if institution else "Institution",
                    degree=degree.title(),
                    field_of_study=field,
                    start_year=start_year,
                    end_year=end_year,
                ))
                if len(education_entries) >= 3:
                    break

        return education_entries

    @staticmethod
    def _extract_certifications(raw_text: str) -> List[CertificationDTO]:
        """Extract professional certifications from resume."""
        certs: List[CertificationDTO] = []
        seen_names: set = set()

        # High-precision cert patterns — look for known cert keywords in concise lines
        cert_name_patterns = [
            # AWS/Azure/GCP certs
            r"(AWS\s+(?:Certified)?\s+[A-Z][\w\s]+(?:Associate|Professional|Specialty|Practitioner))",
            r"(Microsoft\s+(?:Certified|Azure)[:\s]+[A-Z][\w\s]+)",
            r"(Google\s+(?:Certified|Cloud)[:\s]+[A-Z][\w\s]+)",
            # Finance certs
            r"(CFA\s+(?:Level\s+\d|Charter)?(?:\s+(?:Passed|Cleared|Completed|Candidate))?)",
            r"(CPA|ACCA|CMA|FRM|CFP|Series\s+\d+|FINRA)",
            r"(Chartered\s+(?:Financial|Accountant|Institute)[\w\s]*)",
            # Project Management
            r"(PMP|CAPM|PMI-ACP|PRINCE2|SAFe\s+\d?|CSM|Certified\s+Scrum\s+Master)",
            # HR certs
            r"(SHRM[-\s](?:CP|SCP)|PHR|SPHR|CHRP|CIPD)",
            # Security certs
            r"(CISSP|CISA|CISM|CEH|CompTIA\s+\w+|Security\+|Network\+|OSCP)",
            # Cisco / Networking
            r"(CCNA|CCNP|CCIE|CompTIA\s+A\+)",
            # Other
            r"(Six\s+Sigma\s+(?:Green|Black|Yellow)\s+Belt|Lean\s+Six\s+Sigma)",
            r"(LEED\s+(?:GA|AP|Fellow)|LEED\s+Certified)",
            r"(Salesforce\s+(?:Administrator|Developer|Consultant|Certified)[\w\s]*)",
            r"(Certified\s+[A-Z][a-zA-Z\s]{3,50}(?:Professional|Engineer|Analyst|Manager|Specialist|Expert|Practitioner)?)",
        ]

        for pat in cert_name_patterns:
            for match in re.finditer(pat, raw_text, re.IGNORECASE):
                cert_text = match.group(1).strip()
                cert_clean = re.sub(r"\s+", " ", cert_text).strip()
                cert_lower = cert_clean.lower()

                # Filter: must be reasonably short, not a full sentence, not already added
                if (5 < len(cert_clean) < 120 and
                        cert_lower not in seen_names and
                        not re.search(r"[,;]", cert_clean) and
                        len(cert_clean.split()) <= 8):

                    year_context = raw_text[max(0, match.start() - 30):match.end() + 30]
                    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", year_context)
                    year = year_match.group(1) if year_match else None

                    seen_names.add(cert_lower)
                    certs.append(CertificationDTO(
                        name=cert_clean,
                        issuing_organization=None,
                        year=year,
                    ))

            if len(certs) >= 10:
                break

        return certs

    @staticmethod
    def _extract_achievements(raw_text: str) -> List[str]:
        """Extract quantifiable achievements from resume."""
        achievements = []

        # Patterns with numbers/metrics
        metric_pattern = re.compile(
            r"(?:(?:increased|reduced|improved|grew|saved|delivered|managed|led|launched|built|scaled|"
            r"achieved|exceeded|generated|saved|boosted|decreased|optimized)\b[^.\n]{10,120})",
            re.IGNORECASE
        )

        for match in metric_pattern.finditer(raw_text):
            achievement = match.group(0).strip().rstrip(".,;")
            if len(achievement) > 20 and achievement not in achievements:
                achievements.append(achievement)
            if len(achievements) >= 8:
                break

        return achievements

    @staticmethod
    def _extract_languages(raw_text: str) -> List[str]:
        """Extract spoken languages from resume."""
        known_languages = [
            "english", "spanish", "french", "german", "mandarin", "chinese", "japanese",
            "hindi", "arabic", "portuguese", "russian", "italian", "korean", "dutch",
            "swedish", "danish", "norwegian", "polish", "turkish", "tamil", "telugu",
            "kannada", "malayalam", "marathi", "gujarati", "bengali", "urdu"
        ]
        found = []
        text_lower = raw_text.lower()
        for lang in known_languages:
            if re.search(r"\b" + lang + r"\b", text_lower):
                found.append(lang.title())
        return found if found else ["English"]

    @staticmethod
    def _infer_industry_domains(raw_text: str, companies: List[str], work_exp: List[WorkExperienceDTO]) -> List[str]:
        """Infer industry domains from resume context."""
        text_lower = raw_text.lower()

        domain_signals = {
            "FinTech / Banking": ["bank", "fintech", "financial services", "trading", "investment", "insurance", "payments"],
            "Healthcare / MedTech": ["hospital", "clinic", "healthcare", "medical", "pharma", "biotech", "ehr", "hipaa"],
            "E-Commerce / Retail": ["e-commerce", "ecommerce", "retail", "shopify", "marketplace", "amazon"],
            "SaaS / Enterprise Software": ["saas", "b2b", "platform", "cloud software", "enterprise"],
            "Data & Analytics": ["analytics", "data engineering", "business intelligence", "bi platform"],
            "Cybersecurity": ["security", "soc", "siem", "penetration testing", "infosec"],
            "HR Tech / Talent": ["recruitment", "talent acquisition", "hris", "workforce"],
            "Legal Tech": ["law firm", "legal services", "litigation", "contract management"],
            "Supply Chain / Logistics": ["logistics", "supply chain", "warehouse", "freight", "distribution"],
            "Real Estate / PropTech": ["real estate", "property", "proptech", "construction"],
            "Media / AdTech": ["media", "advertising", "digital marketing", "content", "publishing"],
            "Manufacturing / Industrial": ["manufacturing", "industrial", "factory", "production", "engineering"],
            "Education / EdTech": ["education", "edtech", "university", "school", "learning", "training"],
        }

        detected = []
        for domain, signals in domain_signals.items():
            if any(sig in text_lower for sig in signals):
                detected.append(domain)

        return detected[:5] if detected else ["General Professional Services"]

    @staticmethod
    def _fallback_parse(raw_text: str) -> ResumeStructuredExtract:
        """Comprehensive heuristic NLP engine for resume parsing without LLM."""
        logger.info("Running heuristic resume parser on raw text...")

        # Contact info
        contact = ResumeParserService._extract_contact(raw_text)

        # Professional summary
        summary = ResumeParserService._extract_summary(raw_text)

        # Work experience
        work_exp, companies, total_exp_years = ResumeParserService._extract_work_experience(raw_text)

        # Education
        education = ResumeParserService._extract_education(raw_text)

        # Skills (from full resume using taxonomy)
        mand_raw, good_raw = SkillTaxonomyService.extract_skills_from_text(raw_text)
        all_skills_raw = mand_raw + good_raw

        extracted_skills = [
            SkillItemDTO(name=s["name"], category=s["category"])
            for s in all_skills_raw
        ]

        # Add skills from work experience bullets that may have been missed
        work_skill_names = {s.name.lower() for s in extracted_skills}
        for exp in work_exp:
            for skill_name in exp.skills_used:
                if skill_name.lower() not in work_skill_names:
                    extracted_skills.append(SkillItemDTO(name=skill_name, category="Domain Competency"))
                    work_skill_names.add(skill_name.lower())

        extracted_skills = ResumeParserService._clean_extracted_skills(extracted_skills, raw_text=raw_text, candidate_name=contact["name"])
        if not extracted_skills:
            extracted_skills = []

        # Certifications
        certifications = ResumeParserService._extract_certifications(raw_text)

        # Achievements
        achievements = ResumeParserService._extract_achievements(raw_text)

        # Languages
        languages = ResumeParserService._extract_languages(raw_text)

        # Industry domains
        industry_domains = ResumeParserService._infer_industry_domains(raw_text, companies, work_exp)

        logger.info(
            f"Heuristic resume parser extracted: name='{contact['name']}', "
            f"exp={total_exp_years}yrs, skills={len(extracted_skills)}, "
            f"work_entries={len(work_exp)}, edu={len(education)}, certs={len(certifications)}"
        )

        return ResumeStructuredExtract(
            name=contact["name"][:100],
            email=contact["email"],
            phone=contact["phone"],
            location=contact["location"],
            linkedin_url=contact["linkedin_url"],
            github_url=contact["github_url"],
            portfolio_url=contact["portfolio_url"],
            summary=summary,
            total_experience_years=total_exp_years,
            work_experience=work_exp,
            education=education,
            skills=extracted_skills,
            companies=companies,
            projects=[],
            certifications=certifications,
            achievements=achievements,
            languages=languages,
            publications=[],
        )
