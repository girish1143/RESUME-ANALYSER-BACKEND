from pydantic import BaseModel, Field


class ProjectAnalysis(BaseModel):
    title: str
    score: int = Field(ge=0, le=100)
    detected_skills: list[str]
    strengths: list[str]
    improvements: list[str]
    evidence: str


class ResumeAnalysis(BaseModel):
    analysis_source: str = "local_nlp"
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    score: int = Field(ge=0, le=100)
    summary: str
    llm_report: str
    strengths: list[str]
    gaps: list[str]
    extracted_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    suitable_roles: list[str]
    project_scores: list[ProjectAnalysis]
