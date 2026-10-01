from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResearchFact(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    category: Literal[
        "location",
        "transport",
        "hotel_facility",
        "room_amenity",
        "nearby_attraction",
        "policy",
    ]
    claim: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    section: str = Field(min_length=1)
    caveats: list[str]
class ResearchWarning(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    issue: str = Field(min_length=1)
    evidence: list[str] = Field(min_length=1)

class SourceResearch(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    identity_status: Literal["matched", "uncertain", "mismatch"]
    identity_reason: str = Field(min_length=1)
    facts: list[ResearchFact]
    warnings: list[ResearchWarning]