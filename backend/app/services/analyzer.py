from app.schemas import ResumeAnalysis
from app.services.llm import analyze_with_llm, has_llm_config
from app.services.nlp import (
    analyze_projects,
    compare_with_job,
    extract_contact_info,
    extract_skills,
    keyword_highlights,
    score_resume,
)


async def analyze_resume(resume_text: str, job_description: str | None = None) -> ResumeAnalysis:
    if len(resume_text.strip()) < 80:
        raise ValueError("The resume text is too short to analyze.")

    baseline = _build_baseline(resume_text, job_description)
    if not has_llm_config():
        return baseline

    try:
        return await analyze_with_llm(resume_text, job_description, baseline)
    except Exception as exc:
        baseline.gaps.append("Gemini LLM analysis failed, so this report used the local NLP fallback.")
        baseline.recommendations.append("Check GEMINI_API_KEY, GEMINI_MODEL, and internet access if you expected an LLM report.")
        baseline.llm_report = f"Local fallback report. Gemini could not complete the request: {type(exc).__name__}."
        return baseline


def _build_baseline(resume_text: str, job_description: str | None) -> ResumeAnalysis:
    contact = extract_contact_info(resume_text)
    skills = extract_skills(resume_text)
    comparison = compare_with_job(resume_text, job_description)
    score = score_resume(resume_text, job_description)
    keywords = keyword_highlights(resume_text)
    project_scores = analyze_projects(resume_text)

    gaps = []
    recommendations = []

    if not contact["email"]:
        gaps.append("No email address was detected.")
        recommendations.append("Add a professional email address near the top of the resume.")
    if not skills:
        gaps.append("Few technical skills were detected.")
        recommendations.append("Add a dedicated skills section with tools, languages, frameworks, and databases.")
    if comparison["missing_skills"]:
        gaps.append("Some job description skills are missing from the resume.")
        recommendations.append("Add relevant project or experience bullets for the missing job skills you actually have.")

    if len(resume_text.split()) < 250:
        gaps.append("Resume content appears brief.")
        recommendations.append("Expand experience and project bullets with impact, metrics, and technologies used.")
    if not project_scores:
        gaps.append("No clear project section was detected.")
        recommendations.append("Add a projects section with project title, tech stack, features, GitHub/demo link, and impact.")
    elif any(project.score < 70 for project in project_scores):
        recommendations.append("Improve lower-scoring projects by adding tech stack, specific features, impact, and links.")

    strengths = []
    if contact["email"]:
        strengths.append("Contact information is easy to identify.")
    if skills:
        strengths.append(f"Detected technical skills: {', '.join(skills[:8])}.")
    if comparison["matched_skills"]:
        strengths.append("Resume matches several skills from the job description.")

    if not strengths:
        strengths.append("The resume has enough text to perform an initial analysis.")

    if not recommendations:
        recommendations.append("Make each experience bullet action-oriented and include measurable outcomes where possible.")
        recommendations.append("Tailor the top summary and skills section to the target job.")

    return ResumeAnalysis(
        analysis_source="local_nlp",
        candidate_name=contact["candidate_name"],
        email=contact["email"],
        phone=contact["phone"],
        score=score,
        summary=_summary(score, keywords),
        llm_report=_local_report(score, skills, project_scores),
        strengths=strengths,
        gaps=gaps or ["No major gaps detected by the local NLP pass."],
        extracted_skills=skills,
        matched_skills=comparison["matched_skills"],
        missing_skills=comparison["missing_skills"],
        recommendations=recommendations,
        suitable_roles=_roles_from_skills(skills),
        project_scores=project_scores,
    )


def _summary(score: int, keywords: list[str]) -> str:
    keyword_text = ", ".join(keywords[:6]) if keywords else "general resume content"
    if score >= 80:
        return f"Strong resume foundation with relevant keywords around {keyword_text}."
    if score >= 55:
        return f"Good starting resume, but it can be sharpened for ATS and job relevance. Key terms include {keyword_text}."
    return f"The resume needs stronger structure, clearer skills, and more job-targeted detail. Current keywords include {keyword_text}."


def _local_report(score: int, skills: list[str], project_scores: list) -> str:
    project_count = len(project_scores)
    skill_text = ", ".join(skills[:10]) if skills else "few technical skills detected"
    return (
        f"Local NLP report: overall resume score is {score}/100. "
        f"Detected skills include {skill_text}. "
        f"Detected {project_count} project entry{'ies' if project_count != 1 else 'y'} for project-level scoring. "
        "Add measurable impact, clear ownership, tech stack, and proof links to improve the report."
    )


def _roles_from_skills(skills: list[str]) -> list[str]:
    skill_set = set(skills)
    roles = []
    if {"react", "javascript"} & skill_set:
        roles.append("Frontend Developer")
    if {"python", "fastapi", "django", "flask"} & skill_set:
        roles.append("Backend Developer")
    if {"machine learning", "nlp", "pandas", "numpy"} & skill_set:
        roles.append("Data Science / ML Intern")
    if {"sql", "power bi", "tableau", "excel"} & skill_set:
        roles.append("Data Analyst")
    if {"langchain", "llm", "openai"} & skill_set:
        roles.append("AI Engineer Intern")
    return roles or ["Software Developer Intern", "Technical Trainee"]
