import json
import re
from typing import Dict, List, Optional, Set, Tuple
from loguru import logger
import openai

from app.core.config import settings
from app.prompts.semantic_matcher import get_semantic_matcher_prompt
from app.schemas.matching import MatchType, SemanticMatchRequest, SemanticMatchResponse, SkillMatchDetail
from app.services.embedding_service import EmbeddingService


class SemanticMatcherService:
    """AI Service for semantic skill and domain taxonomy matching.

    Matching pipeline (no-API fallback):
    1. Exact match — skill name appears in candidate's skill list
    2. Alias/synonym match — using 300+ curated technology aliases
    3. Substring / partial token match — "Apache Spark" in "PySpark" context
    4. Raw text mention — skill appears anywhere in the resume raw text (whole word)
    5. NOT FOUND — marked MISSING with 0 score
    """

    # ─── Comprehensive 300+ skill alias map ──────────────────────────────────
    TAXONOMY_SYNONYMS: Dict[str, List[str]] = {
        # Python ecosystem
        "python": ["pyspark", "pandas", "numpy", "scipy", "fastapi", "django", "flask", "jupyter", "python3", "python 3"],
        "pyspark": ["apache spark", "spark", "pyspark", "spark streaming"],
        "apache spark": ["pyspark", "spark", "apache spark", "spark sql", "spark streaming"],
        "pandas": ["dataframe", "python pandas"],
        "numpy": ["numpy arrays", "numerical python"],
        # Data Engineering
        "apache airflow": ["airflow", "airflow dags", "workflow orchestration", "apache airflow"],
        "airflow": ["apache airflow", "airflow dags", "prefect", "dagster"],
        "apache kafka": ["kafka", "kafka streaming", "event streaming", "kafka topics"],
        "kafka": ["apache kafka", "kafka streaming", "event streaming", "aws kinesis"],
        "dbt": ["data build tool", "dbt core", "dbt cloud", "dbt models"],
        "delta lake": ["delta tables", "apache delta", "delta format", "databricks delta"],
        "apache iceberg": ["iceberg tables", "iceberg format"],
        "fivetran": ["data integration", "elt tool"],
        # Databases / SQL
        "sql": ["postgresql", "mysql", "tsql", "sqlite", "hive sql", "spark sql", "database queries", "relational database"],
        "postgresql": ["postgres", "pg", "postgresql database"],
        "mysql": ["mariadb", "mysql database"],
        "snowflake": ["snowflake data warehouse", "snowflake cloud"],
        "redshift": ["aws redshift", "amazon redshift"],
        "bigquery": ["google bigquery", "bq", "big query", "gcp bigquery"],
        "google bigquery": ["bigquery", "bq", "big query"],
        "databricks": ["databricks platform", "azure databricks", "databricks lakehouse"],
        "oracle": ["oracle database", "oracle sql", "oracle db", "pl/sql"],
        # Cloud platforms
        "aws": ["amazon web services", "amazon aws", "aws cloud", "cloud aws"],
        "gcp": ["google cloud platform", "google cloud", "gcp cloud"],
        "google cloud platform": ["gcp", "google cloud", "gcp cloud"],
        "azure": ["microsoft azure", "azure cloud", "ms azure"],
        # Healthcare & Clinical
        "hl7": ["hl7 v2", "hl7 fhir", "health level 7", "hl7 messages"],
        "hl7 v2": ["hl7", "adt messages", "health level 7 v2", "hl7 2.x"],
        "fhir": ["fhir r4", "fhir stu3", "smart on fhir", "fhir apis", "hl7 fhir"],
        "fhir r4": ["fhir", "fhir r4 api", "smart on fhir"],
        "hipaa": ["hipaa compliance", "phi", "hipaa security", "hipaa privacy", "phi data"],
        "icd-10": ["icd10", "icd 10", "diagnosis codes", "medical coding"],
        "cpt": ["cpt codes", "procedure codes", "current procedural terminology"],
        "loinc": ["loinc codes", "laboratory codes"],
        "epic ehr": ["epic", "epic clarity", "epic caboodle", "epic systems", "epic emr"],
        "cerner": ["cerner millennium", "oracle cerner", "cerner ehr"],
        # Payments / FinTech
        "ach": ["automated clearing house", "ach payments", "bank transfer", "nacha"],
        "real-time payments": ["rtp", "fednow", "real time payments", "instant payments"],
        "rtp": ["real-time payments", "fednow", "instant payments"],
        "fednow": ["rtp", "real-time payments", "fed now"],
        "pci-dss": ["pci dss", "pci compliance", "payment card industry", "pci"],
        "aml": ["anti-money laundering", "aml compliance", "bsa/aml"],
        "kyc": ["know your customer", "kyc verification", "identity verification"],
        "aml/kyc": ["anti-money laundering", "know your customer", "compliance", "aml", "kyc"],
        "fraud detection": ["fraud prevention", "fraud risk", "chargeback prevention", "risk management"],
        "payment apis": ["payment gateway", "rest api payments", "stripe api", "payment integration"],
        "visa": ["visa network", "visa card", "visa mastercard", "card network"],
        "mastercard": ["mc", "card network", "visa mastercard"],
        # BI / Analytics
        "tableau": ["tableau desktop", "tableau server", "tableau public", "data visualization"],
        "power bi": ["powerbi", "microsoft bi", "power bi desktop", "dax", "powerquery"],
        "amplitude": ["product analytics", "user analytics", "amplitude analytics"],
        "mixpanel": ["product analytics", "event tracking", "user analytics"],
        "looker": ["looker studio", "google looker", "looker dashboards"],
        # ML / AI
        "machine learning": ["ml", "predictive modeling", "supervised learning", "scikit-learn", "sklearn"],
        "scikit-learn": ["sklearn", "machine learning", "scikit learn", "python ml"],
        "pytorch": ["torch", "pytorch framework", "deep learning pytorch"],
        "tensorflow": ["tf", "tensorflow keras", "deep learning tf", "keras"],
        "mlflow": ["ml experiment tracking", "model registry", "mlflow tracking"],
        # DevOps / Infrastructure
        "docker": ["containerization", "docker containers", "dockerfile", "container orchestration"],
        "kubernetes": ["k8s", "kubernetes orchestration", "container orchestration", "helm"],
        "apache": ["apache software", "apache foundation"],
        # Product Management
        "agile": ["scrum", "kanban", "sprint planning", "agile methodology"],
        "scrum": ["agile", "sprint", "scrum master", "agile scrum"],
        "prd": ["product requirements document", "prds", "product specs", "user stories"],
        "okr": ["objectives and key results", "okrs", "goal setting"],
        "stakeholder management": ["cross-functional collaboration", "executive communication", "alignment"],
        # Programming languages
        "javascript": ["js", "node.js", "nodejs", "typescript", "es6"],
        "typescript": ["ts", "javascript typescript"],
        "java": ["spring boot", "java spring", "jvm"],
        "scala": ["apache spark scala", "functional programming"],
        "r": ["r programming", "rstudio", "tidyverse"],
        "go": ["golang"],
        # General engineering
        "rest api": ["restful api", "rest apis", "api design", "http api", "web services"],
        "api design": ["rest api", "api architecture", "swagger", "openapi"],
        "etl": ["extract transform load", "data pipelines", "data integration", "etl pipelines"],
        "data pipelines": ["etl", "data workflows", "pipeline engineering"],
        "data modeling": ["data warehouse design", "dimensional modeling", "schema design"],
        "data lake": ["data lake architecture", "lakehouse", "s3 data lake"],
        # Finance domain
        "financial modeling": ["financial analysis", "financial forecasting", "valuation models"],
        "sql server": ["mssql", "microsoft sql server", "t-sql"],
        "excel": ["microsoft excel", "vba", "spreadsheet", "pivot tables"],
    }

    # Build a reverse lookup: alias → canonical
    _ALIAS_TO_CANONICAL: Dict[str, str] = {}
    for _canon, _aliases in TAXONOMY_SYNONYMS.items():
        for _alias in _aliases:
            _ALIAS_TO_CANONICAL[_alias.lower()] = _canon.lower()

    @staticmethod
    async def match_skills(request: SemanticMatchRequest, version: str = "v1") -> SemanticMatchResponse:
        """Perform deep semantic skill matching via LLM or multi-strategy fallback."""
        if settings.OPENAI_API_KEY:
            try:
                return await SemanticMatcherService._openai_semantic_match(request, version=version)
            except Exception as e:
                logger.error(f"OpenAI Semantic Matcher failed: {str(e)}. Using taxonomy & fallback engine.")

        return await SemanticMatcherService._heuristic_match(request)

    @staticmethod
    async def _openai_semantic_match(request: SemanticMatchRequest, version: str = "v1") -> SemanticMatchResponse:
        system_prompt = get_semantic_matcher_prompt(version=version)
        user_prompt = f"""
        Required Job Skills: {json.dumps(request.required_skills)}
        Candidate Resume Skills: {json.dumps(request.candidate_skills)}
        Candidate Experience Summary: {(request.candidate_experience_text or '')[:2000]}
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
        return SemanticMatchResponse(**parsed_dict)

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase and strip punctuation for matching."""
        return re.sub(r"[^a-z0-9\s\+\#\./\-]", "", text.lower()).strip()

    @staticmethod
    def _get_tokens(text: str) -> Set[str]:
        """Split text into individual tokens for partial matching."""
        return set(SemanticMatcherService._normalize(text).split())

    @staticmethod
    def _candidate_lookup_sets(
        candidate_skills: List[str],
        candidate_text: str,
    ) -> Tuple[Set[str], Set[str], str]:
        """Build fast lookup sets from candidate data."""
        # Skill name lookup (exact)
        skills_exact: Set[str] = {SemanticMatcherService._normalize(s) for s in candidate_skills}

        # Token set from all skill names combined (for partial matching)
        all_skill_tokens: Set[str] = set()
        for s in candidate_skills:
            all_skill_tokens.update(SemanticMatcherService._get_tokens(s))

        text_lower = candidate_text.lower()
        return skills_exact, all_skill_tokens, text_lower

    @staticmethod
    async def _heuristic_match(request: SemanticMatchRequest) -> SemanticMatchResponse:
        """
        Multi-strategy heuristic skill matching engine:
        1. Exact normalized match against candidate skills
        2. Synonym/alias resolution through TAXONOMY_SYNONYMS
        3. Substring / partial token match
        4. Whole-word match against raw resume text (with a confidence penalty)
        5. MISSING — not found anywhere
        """
        details: List[SkillMatchDetail] = []
        total_score = 0.0

        skills_exact, skill_tokens, cand_text_lower = \
            SemanticMatcherService._candidate_lookup_sets(
                request.candidate_skills,
                request.candidate_experience_text or "",
            )

        alias_map = SemanticMatcherService._ALIAS_TO_CANONICAL
        synonym_map = SemanticMatcherService.TAXONOMY_SYNONYMS

        # Pre-build reverse alias lookup from candidate skills
        cand_aliases: Set[str] = set()
        for s in request.candidate_skills:
            s_norm = SemanticMatcherService._normalize(s)
            cand_aliases.add(s_norm)
            # Also add synonyms of each candidate skill to the lookup
            if s_norm in synonym_map:
                for syn in synonym_map[s_norm]:
                    cand_aliases.add(syn.lower())
            if s_norm in alias_map:
                canonical = alias_map[s_norm]
                cand_aliases.add(canonical)
                if canonical in synonym_map:
                    for syn in synonym_map[canonical]:
                        cand_aliases.add(syn.lower())

        # Build sentence index helper for evidence citations
        raw_exp = request.candidate_experience_text or ""
        # Split into sentences keeping offsets
        sentences_with_offsets = []
        for m in re.finditer(r'[^.!?]+[.!?]?', raw_exp):
            sent = m.group(0)
            if len(sent.strip()) > 5:
                sentences_with_offsets.append((sent, m.start(), m.end()))

        def _find_evidence(keyword: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
            kw_pat = r"\b" + re.escape(keyword.lower()) + r"\b"
            for s, start, end in sentences_with_offsets:
                if re.search(kw_pat, s.lower()):
                    return s.strip(), start, end
            # fallback substring
            for s, start, end in sentences_with_offsets:
                if keyword.lower() in s.lower():
                    return s.strip(), start, end
            return None, None, None

        # Check if candidate is HR/Talent Acquisition profile
        is_hr_profile = False
        if request.candidate_experience_text:
            text_lower = request.candidate_experience_text.lower()
            hr_keywords = {"recruiter", "talent acquisition", "human resources", "hr specialist", "hiring", "recruit"}
            if any(kw in text_lower for kw in hr_keywords):
                is_hr_profile = True

        tech_blacklist = {
            "ci/cd", "c#", "java", "python", "kubernetes", "docker", "aws", "gcp", "azure", 
            "c++", "javascript", "react", "node.js", "typescript", "git", "real estate", "real-estate",
            "c-sharp", "golang", "devops", "sql server", "mysql"
        }

        for req_skill in request.required_skills:
            req_norm = SemanticMatcherService._normalize(req_skill)
            req_tokens = SemanticMatcherService._get_tokens(req_skill)

            # Prevent tech keywords matching on HR candidate profiles
            if is_hr_profile and any(tech in req_norm for tech in tech_blacklist):
                details.append(SkillMatchDetail(
                    required_skill=req_skill,
                    matched_candidate_skill=None,
                    match_type=MatchType.MISSING,
                    similarity_score=0.0,
                    reasoning=f"Irrelevant tech/real-estate skill ignored for Human Resources profile.",
                    evidence_sentence=None,
                    char_start=None,
                    char_end=None,
                ))
                continue

            # ── Strategy 1: Exact match in candidate skill list ──────────────
            if req_norm in skills_exact:
                evidence, start, end = _find_evidence(req_skill)
                details.append(SkillMatchDetail(
                    required_skill=req_skill,
                    matched_candidate_skill=req_skill,
                    match_type=MatchType.EXACT,
                    similarity_score=1.0,
                    reasoning=f"Exact match: '{req_skill}' found in candidate's skill list.",
                    evidence_sentence=evidence,
                    char_start=start,
                    char_end=end,
                ))
                total_score += 100.0
                continue

            # ── Strategy 2: Alias/synonym resolution ────────────────────────
            synonyms_to_check: Set[str] = set()
            if req_norm in synonym_map:
                synonyms_to_check.update(s.lower() for s in synonym_map[req_norm])
            if req_norm in alias_map:
                canonical = alias_map[req_norm]
                synonyms_to_check.add(canonical)
                if canonical in synonym_map:
                    synonyms_to_check.update(s.lower() for s in synonym_map[canonical])

            matched_via_synonym = None
            for syn in synonyms_to_check:
                if syn in skills_exact or syn in cand_aliases:
                    matched_via_synonym = syn
                    break

            if matched_via_synonym:
                evidence, start, end = _find_evidence(matched_via_synonym)
                details.append(SkillMatchDetail(
                    required_skill=req_skill,
                    matched_candidate_skill=matched_via_synonym,
                    match_type=MatchType.SEMANTIC,
                    similarity_score=0.92,
                    reasoning=f"Synonym match: '{req_skill}' resolved to '{matched_via_synonym}' in candidate's profile.",
                    evidence_sentence=evidence,
                    char_start=start,
                    char_end=end,
                ))
                total_score += 92.0
                continue

            # ── Strategy 3: Partial token match (multi-token skills) ─────────
            if len(req_tokens) >= 2:
                overlap = req_tokens & skill_tokens
                coverage = len(overlap) / len(req_tokens)
                if coverage >= 0.75:
                    matched_word = list(overlap)[0]
                    evidence, start, end = _find_evidence(matched_word)
                    details.append(SkillMatchDetail(
                        required_skill=req_skill,
                        matched_candidate_skill=" ".join(sorted(overlap)),
                        match_type=MatchType.CONCEPTUAL,
                        similarity_score=round(0.75 + 0.15 * coverage, 2),
                        reasoning=f"Partial token match: {int(coverage*100)}% of '{req_skill}' tokens found in candidate skills.",
                        evidence_sentence=evidence,
                        char_start=start,
                        char_end=end,
                    ))
                    total_score += (0.75 + 0.15 * coverage) * 100.0
                    continue

            # ── Strategy 4: Whole-word match in raw resume text ──────────────
            pattern = r"\b" + re.escape(req_norm) + r"\b"
            if re.search(pattern, cand_text_lower):
                evidence, start, end = _find_evidence(req_norm)
                details.append(SkillMatchDetail(
                    required_skill=req_skill,
                    matched_candidate_skill=f"(mentioned in resume text)",
                    match_type=MatchType.CONCEPTUAL,
                    similarity_score=0.65,
                    reasoning=f"Resume text mention: '{req_skill}' found in candidate's resume text (not declared as skill).",
                    evidence_sentence=evidence,
                    char_start=start,
                    char_end=end,
                ))
                total_score += 65.0
                continue

            # ── Strategy 5: Single meaningful token in skill list ────────────
            meaningful_tokens = {t for t in req_tokens if len(t) >= 4}
            matched_tok = None
            for token in meaningful_tokens:
                if token in skill_tokens:
                    matched_tok = token
                    break
            if matched_tok:
                evidence, start, end = _find_evidence(matched_tok)
                details.append(SkillMatchDetail(
                    required_skill=req_skill,
                    matched_candidate_skill=f"(token '{matched_tok}' matched)",
                    match_type=MatchType.CONCEPTUAL,
                    similarity_score=0.60,
                    reasoning=f"Token match: core keyword '{matched_tok}' from '{req_skill}' found in candidate's skills.",
                    evidence_sentence=evidence,
                    char_start=start,
                    char_end=end,
                ))
                total_score += 60.0
                continue

            # ── Strategy 6: MISSING ──────────────────────────────────────
            details.append(SkillMatchDetail(
                required_skill=req_skill,
                matched_candidate_skill=None,
                match_type=MatchType.MISSING,
                similarity_score=0.0,
                reasoning=f"NOT FOUND: '{req_skill}' was not detected in candidate's skills, synonyms, or resume text.",
            ))

        n = len(request.required_skills)
        overall_score = round(total_score / n, 1) if n > 0 else 0.0

        matched = sum(1 for d in details if d.match_type != MatchType.MISSING)
        logger.debug(
            f"Heuristic skill match: {matched}/{n} skills matched. "
            f"Overall score: {overall_score}/100"
        )

        return SemanticMatchResponse(
            semantic_matches=details,
            overall_semantic_score=overall_score,
        )
