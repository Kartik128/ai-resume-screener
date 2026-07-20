import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SkillBase(BaseModel):
    name: str = Field(..., max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    synonyms: Optional[List[str]] = Field(default_factory=list)


class SkillCreate(SkillBase):
    pass


class SkillRead(SkillBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ExtractedSkill(BaseModel):
    name: str
    category: Optional[str] = None
    synonyms: Optional[List[str]] = Field(default_factory=list)
