import json
import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.schemas import ResumeAnalysis


def has_llm_config() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


async def analyze_with_llm(
    resume_text: str,
    job_description: str | None,
    baseline: ResumeAnalysis,
) -> ResumeAnalysis:
    parser = JsonOutputParser(pydantic_object=ResumeAnalysis)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert technical recruiter, ATS reviewer, and resume coach. "
                "Analyze the resume deeply and return only valid JSON matching the requested schema. "
                "Set analysis_source to 'gemini_llm'. "
                "Write llm_report as a polished recruiter-style report in 120-180 words. "
                "For every project_scores item, score the project independently for clarity, technical depth, "
                "impact, ownership, links/proof, and job relevance.",
            ),
            (
                "human",
                """
Analyze this resume for clarity, relevance, ATS readiness, project quality, and job fit.

Use the baseline NLP findings where useful, but produce your own final report and scoring.
Keep all scores between 0 and 100.
If job description is provided, compare the resume against it.

Resume:
{resume_text}

Job description:
{job_description}

Baseline:
{baseline_json}

Schema:
{format_instructions}
""",
            ),
        ]
    )

    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
    )
    chain = prompt | model | parser
    result = await chain.ainvoke(
        {
            "resume_text": resume_text[:12000],
            "job_description": (job_description or "Not provided")[:6000],
            "baseline_json": baseline.model_dump_json(),
            "format_instructions": parser.get_format_instructions(),
        }
    )

    if isinstance(result, str):
        result = json.loads(result)
    return ResumeAnalysis.model_validate(result)
