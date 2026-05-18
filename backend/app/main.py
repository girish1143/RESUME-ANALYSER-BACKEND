import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ResumeAnalysis
from app.services.analyzer import analyze_resume
from app.services.parser import extract_resume_text

load_dotenv()

app = FastAPI(title="Resume Analyzer API", version="1.0.0")

allowed_origin = os.getenv("ALLOWED_ORIGIN", "http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin, "http://localhost:5173", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=ResumeAnalysis)
async def analyze(
    resume: UploadFile | None = File(default=None),
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    job_description: str | None = Form(default=None),
) -> ResumeAnalysis:
    try:
        upload = resume or file
        if upload:
            resume_text = await extract_resume_text(upload)
        elif text and text.strip():
            resume_text = text.strip()
        else:
            raise ValueError("Upload a resume file or paste resume text.")
        return await analyze_resume(resume_text, job_description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Resume analysis failed.") from exc
