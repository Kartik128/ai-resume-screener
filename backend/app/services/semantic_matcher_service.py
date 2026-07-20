import json
from typing import List, Optional
from loguru import logger
import openai

from app.core.config import settings
from app.prompts.semantic_matcher import get_semantic_matcher_prompt
from app.schemas.matching import MatchType, SemanticMatchRequest, SemanticMatchResponse, SkillMatchDetail
from app.services.embedding_service import EmbeddingService


class SemanticMatcherService:
    """AI Service for semantic skill and domain taxonomy matching without relying on keyword matches."""

    TAXONOMY_SYNONYMS = {
        "power bi": ["microsoft bi", "business intelligence dashboard", "powerquery", "dax", "ssrs", "tableau"],
        "people analytics": ["hr analytics", "workforce analytics", "human capital data", "hris reporting"],
        "react": ["next.js", "redux", "frontend engineering", "javascript ui", "react.js"],
        "python": ["django", "fastapi", "pandas", "pyspark", "flask"],
        "sql": ["postgresql", "mysql", "tsql", "sqlite", "database design", "database"],
    }

    @staticmethod
    async def match_skills(request: SemanticMatchRequest, version: str = "v1") -> SemanticMatchResponse:
        """Perform deep semantic skill matching via LLM or vector/taxonomy fallback."""
        if settings.OPENAI_API_KEY:
            try:
                return await SemanticMatcherService._openai_semantic_match(request, version=version)
            except Exception as e:
                logger.error(f"OpenAI Semantic Matcher failed: {str(e)}. Using taxonomy & vector fallback engine.")

        return await SemanticMatcherService._vector_taxonomy_match(request)

    @staticmethod
    async def _openai_semantic_match(request: SemanticMatchRequest, version: str = "v1") -> SemanticMatchResponse:
        system_prompt = get_semantic_matcher_prompt(version=version)
        user_prompt = f"""
        Required Job Skills: {json.dumps(request.required_skills)}
        Candidate Resume Skills: {json.dumps(request.candidate_skills)}
        Candidate Experience Summary: {request.candidate_experience_text or 'Not provided'}
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
    async def _vector_taxonomy_match(request: SemanticMatchRequest) -> SemanticMatchResponse:
        """Heuristic and vector embedding fallback engine for semantic matching."""
        details: List[SkillMatchDetail] = []

        candidate_skills_lower = [s.lower().strip() for s in request.candidate_skills]
        cand_text_lower = (request.candidate_experience_text or "").lower()

        matched_count = 0
        total_score_acc = 0.0

        for req_skill in request.required_skills:
            req_clean = req_skill.lower().strip()

            # 1. Exact Match Check
            if req_clean in candidate_skills_lower or req_clean in cand_text_lower:
                details.append(
                    SkillMatchDetail(
                        required_skill=req_skill,
                        matched_candidate_skill=req_skill,
                        match_type=MatchType.EXACT,
                        similarity_score=1.0,
                        reasoning=f"Exact match found for '{req_skill}' in candidate skills.",
                    )
                )
                matched_count += 1
                total_score_acc += 100.0
                continue

            # 2. Taxonomy Synonym Check (e.g. Power BI -> Microsoft BI, DAX)
            matched_synonym = None
            for key, syns in SemanticMatcherService.TAXONOMY_SYNONYMS.items():
                if req_clean == key or req_clean in syns:
                    for cand_skill in candidate_skills_lower:
                        if cand_skill == key or cand_skill in syns:
                            matched_synonym = cand_skill
                            break

            if matched_synonym:
                details.append(
                    SkillMatchDetail(
                        required_skill=req_skill,
                        matched_candidate_skill=matched_synonym,
                        match_type=MatchType.SEMANTIC,
                        similarity_score=0.9,
                        reasoning=f"Semantic taxonomy match: '{req_skill}' maps directly to candidate skill '{matched_synonym}'.",
                    )
                )
                matched_count += 1
                total_score_acc += 90.0
                continue

            # 3. Vector Embedding Cosine Similarity Check
            req_vec = await EmbeddingService.get_embedding(req_skill)
            best_cand_skill = None
            best_sim = 0.0

            for cand_skill in request.candidate_skills:
                cand_vec = await EmbeddingService.get_embedding(cand_skill)
                sim = EmbeddingService.cosine_similarity(req_vec, cand_vec)
                if sim > best_sim:
                    best_sim = sim
                    best_cand_skill = cand_skill

            if best_sim >= 0.70 and best_cand_skill:
                details.append(
                    SkillMatchDetail(
                        required_skill=req_skill,
                        matched_candidate_skill=best_cand_skill,
                        match_type=MatchType.CONCEPTUAL,
                        similarity_score=round(best_sim, 2),
                        reasoning=f"Dense vector embedding similarity of {round(best_sim * 100, 1)}% with candidate skill '{best_cand_skill}'.",
                    )
                )
                matched_count += 1
                total_score_acc += best_sim * 100.0
            else:
                details.append(
                    SkillMatchDetail(
                        required_skill=req_skill,
                        matched_candidate_skill=None,
                        match_type=MatchType.MISSING,
                        similarity_score=0.0,
                        reasoning=f"Required skill '{req_skill}' was not found in candidate skills or experience.",
                    )
                )

        overall_score = (total_score_acc / len(request.required_skills)) if request.required_skills else 0.0

        return SemanticMatchResponse(
            semantic_matches=details,
            overall_semantic_score=round(overall_score, 1),
        )
