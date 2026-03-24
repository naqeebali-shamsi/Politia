from pydantic import BaseModel, field_validator


class CompareRequest(BaseModel):
    politician_ids: list[int]

    @field_validator("politician_ids")
    @classmethod
    def validate_ids(cls, v):
        if len(v) < 2:
            raise ValueError("Need at least 2 politicians to compare")
        if len(v) > 5:
            raise ValueError("Cannot compare more than 5 politicians")
        return v


class CompareScores(BaseModel):
    overall: float | None = None
    participation: float | None = None
    disclosure: float | None = None
    integrity_risk: float | None = None


class CompareActivity(BaseModel):
    avg_attendance: float | None = None
    total_questions: int = 0
    total_debates: int = 0


class CompareDisclosure(BaseModel):
    total_assets: float | None = None
    total_liabilities: float | None = None
    criminal_cases: int | None = None


class CompareEntry(BaseModel):
    id: int
    full_name: str
    party: str | None = None
    state: str | None = None
    chamber: str | None = None
    constituency: str | None = None
    photo_url: str | None = None
    scores: CompareScores | None = None
    activity: CompareActivity | None = None
    disclosure: CompareDisclosure | None = None


class CompareResponse(BaseModel):
    politicians: list[CompareEntry]
