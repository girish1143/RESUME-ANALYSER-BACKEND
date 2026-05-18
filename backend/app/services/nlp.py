import re
from collections import Counter

from app.schemas import ProjectAnalysis


SKILL_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node.js",
    "express",
    "fastapi",
    "django",
    "flask",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "github",
    "machine learning",
    "deep learning",
    "nlp",
    "langchain",
    "llm",
    "openai",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "data analysis",
    "power bi",
    "tableau",
    "excel",
    "rest api",
    "graphql",
    "html",
    "css",
    "tailwind",
    "solidity",
    "ethereum",
    "erc-20",
    "websocket",
}


STOP_WORDS = {
    "and",
    "the",
    "with",
    "for",
    "from",
    "that",
    "this",
    "using",
    "will",
    "have",
    "has",
    "are",
    "was",
    "were",
    "you",
    "your",
    "our",
    "their",
}


def extract_contact_info(text: str) -> dict[str, str | None]:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4}", text)
    name = _guess_name(text)

    return {
        "candidate_name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
    }


def extract_skills(text: str) -> list[str]:
    normalized = _normalize(text)
    found = {skill for skill in SKILL_KEYWORDS if skill in normalized}
    return sorted(found)


def compare_with_job(resume_text: str, job_description: str | None) -> dict[str, list[str]]:
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description or ""))

    if not jd_skills:
        return {
            "matched_skills": [],
            "missing_skills": [],
        }

    return {
        "matched_skills": sorted(resume_skills & jd_skills),
        "missing_skills": sorted(jd_skills - resume_skills),
    }


def score_resume(text: str, job_description: str | None) -> int:
    skills = extract_skills(text)
    contact = extract_contact_info(text)
    section_score = _section_score(text)
    contact_score = 10 if contact["email"] else 0
    skill_score = min(len(skills) * 4, 35)

    if job_description:
        comparison = compare_with_job(text, job_description)
        jd_skills = set(extract_skills(job_description))
        match_ratio = len(comparison["matched_skills"]) / max(len(jd_skills), 1)
        jd_score = round(match_ratio * 30)
    else:
        jd_score = 15

    return min(section_score + contact_score + skill_score + jd_score, 100)


def keyword_highlights(text: str, limit: int = 12) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
    filtered = [word for word in words if word not in STOP_WORDS]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(limit)]


def analyze_projects(text: str) -> list[ProjectAnalysis]:
    projects = _extract_project_blocks(text)
    return [_score_project(project) for project in projects]


def _section_score(text: str) -> int:
    normalized = _normalize(text)
    expected_sections = ["experience", "education", "skills", "projects"]
    present = sum(1 for section in expected_sections if section in normalized)
    return present * 5


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _guess_name(text: str) -> str | None:
    for line in text.splitlines()[:8]:
        cleaned = line.strip()
        if not cleaned or "@" in cleaned or any(char.isdigit() for char in cleaned):
            continue
        words = cleaned.split()
        if 1 < len(words) <= 4 and all(word[:1].isalpha() for word in words):
            return cleaned
    return None


def _extract_project_blocks(text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    project_start = next(
        (index for index, line in enumerate(lines) if re.search(r"\b(projects?|academic projects?|personal projects?)\b", line, re.I)),
        None,
    )
    if project_start is None:
        return []

    section_lines: list[str] = []
    for line in lines[project_start + 1 :]:
        if re.search(r"\b(education|experience|skills|certifications|achievements|summary|objective)\b", line, re.I):
            break
        section_lines.append(line)

    if not section_lines:
        return []

    projects: list[dict[str, str]] = []
    current_title: str | None = None
    current_details: list[str] = []

    for line in section_lines:
        cleaned = re.sub(r"^[•*\-\u2022]+\s*", "", line).strip()
        if not cleaned:
            continue

        looks_like_title = (
            len(cleaned.split()) <= 9
            and not cleaned.endswith(".")
            and not re.match(r"^(built|created|developed|implemented|designed|used|integrated)\b", cleaned, re.I)
        )

        if looks_like_title and current_title:
            projects.append({"title": current_title, "details": " ".join(current_details).strip()})
            current_title = cleaned
            current_details = []
        elif looks_like_title:
            current_title = cleaned
        elif current_title:
            current_details.append(cleaned)
        else:
            current_title = cleaned[:70]

    if current_title:
        projects.append({"title": current_title, "details": " ".join(current_details).strip()})

    return [project for project in projects if project["title"] or project["details"]][:8]


def _score_project(project: dict[str, str]) -> ProjectAnalysis:
    title = re.sub(r"\s+", " ", project["title"]).strip() or "Untitled Project"
    details = project["details"]
    combined = f"{title} {details}".strip()
    normalized = _normalize(combined)
    skills = extract_skills(combined)

    score = 25
    strengths: list[str] = []
    improvements: list[str] = []

    if title and title != "Untitled Project":
        score += 10
        strengths.append("Project title is identifiable.")
    else:
        improvements.append("Add a clear project title.")

    if len(details.split()) >= 18:
        score += 15
        strengths.append("Project has enough detail to understand the work.")
    else:
        improvements.append("Add 2-3 bullets explaining what the project does and your contribution.")

    if skills:
        score += min(len(skills) * 5, 20)
        strengths.append("Technical stack is visible.")
    else:
        improvements.append("Mention the tools, languages, frameworks, and database used.")

    if re.search(r"\b(github|gitlab|demo|live|deployed|hosted|http|www)\b", normalized):
        score += 10
        strengths.append("Project includes a link, deployment, or repository signal.")
    else:
        improvements.append("Add a GitHub or live demo link if available.")

    if re.search(r"\b(\d+%?|\busers?\b|\bms\b|\bseconds?\b|\bapi\b|\bauth\b|\bdashboard\b|\bresponsive\b)\b", normalized):
        score += 15
        strengths.append("Project includes measurable or feature-specific detail.")
    else:
        improvements.append("Add impact, metrics, or specific features such as auth, API, dashboard, or deployment.")

    if re.search(r"\b(team|collaborated|led|owned|designed|built|implemented|integrated)\b", normalized):
        score += 5
        strengths.append("Contribution/action wording is present.")
    else:
        improvements.append("Use action verbs that show your ownership and role.")

    return ProjectAnalysis(
        title=title[:90],
        score=min(score, 100),
        detected_skills=skills,
        strengths=strengths or ["Project is present in the resume."],
        improvements=improvements or ["Project description is strong; keep it concise and outcome-focused."],
        evidence=details[:240] or title[:240],
    )
