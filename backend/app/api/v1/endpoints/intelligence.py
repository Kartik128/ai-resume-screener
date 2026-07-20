from typing import Dict, List
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.matching import SemanticMatchRequest, SemanticMatchResponse
from app.services.embedding_service import EmbeddingService
from app.services.semantic_matcher_service import SemanticMatcherService

router = APIRouter()


@router.post(
    "/semantic-skill-match",
    response_model=SemanticMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform deep semantic skill matching without relying on keyword matches",
)
async def semantic_skill_match(
    body: SemanticMatchRequest,
    current_user: User = Depends(get_current_user),
) -> SemanticMatchResponse:
    return await SemanticMatcherService.match_skills(body)


@router.post(
    "/embed-text",
    response_model=Dict[str, List[float]],
    status_code=status.HTTP_200_OK,
    summary="Generate dense vector embedding for input text string",
)
async def generate_embedding(
    text: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
) -> Dict[str, List[float]]:
    embedding = await EmbeddingService.get_embedding(text)
    return {"text": text, "embedding": embedding}


@router.get(
    "/synonyms",
    response_model=Dict[str, List[str]],
    status_code=status.HTTP_200_OK,
    summary="Fetch semantic taxonomy synonyms for a given skill (e.g. Power BI -> DAX, PowerQuery, MS BI)",
)
async def get_skill_synonyms(
    skill: str = Query(..., description="Skill name to resolve synonyms for"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, List[str]]:
    skill_clean = skill.lower().strip()
    synonyms = SemanticMatcherService.TAXONOMY_SYNONYMS.get(
        skill_clean, [f"{skill} Professional", f"{skill} Expert"]
    )
    return {"skill": skill, "synonyms": synonyms}
