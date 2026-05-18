import { useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  BadgeCheck,
  Brain,
  BriefcaseBusiness,
  ClipboardCheck,
  FileText,
  Loader2,
  Sparkles,
  Upload,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8001";

function App() {
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const requestIdRef = useRef(0);

  const scoreTone = useMemo(() => {
    const score = analysis?.score ?? 0;
    if (score >= 80) return "excellent";
    if (score >= 55) return "good";
    return "needs-work";
  }, [analysis]);

  function handleResumeChange(event) {
    const selectedFile = event.target.files?.[0] ?? null;
    requestIdRef.current += 1;
    setResume(selectedFile);
    setAnalysis(null);
    setError("");
  }

  async function handleAnalyze(event) {
    event.preventDefault();
    if (!resume) {
      setError("Upload a PDF, DOCX, or TXT resume first.");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysis(null);
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("job_description", jobDescription);

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Analysis failed.");
      }
      if (requestId !== requestIdRef.current) {
        return;
      }
      setAnalysis(payload);
    } catch (err) {
      if (requestId !== requestIdRef.current) {
        return;
      }
      setError(err.message);
    } finally {
      if (requestId === requestIdRef.current) {
        setLoading(false);
      }
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="panel input-panel">
          <div className="brand-row">
            <div className="brand-icon">
              <Brain size={24} />
            </div>
            <div>
              <h1>Resume Analyzer</h1>
              <p>LLM + NLP + LangChain</p>
            </div>
          </div>

          <form onSubmit={handleAnalyze} className="form-stack">
            <label className="upload-zone">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleResumeChange}
              />
              <Upload size={28} />
              <span>{resume ? resume.name : "Upload resume"}</span>
              <small>PDF, DOCX, or TXT</small>
            </label>

            <label className="field-group">
              <span>Job description</span>
              <textarea
                value={jobDescription}
                onChange={(event) => setJobDescription(event.target.value)}
                placeholder="Paste a target job description to compare skills and improve match score."
              />
            </label>

            <button className="primary-button" disabled={loading}>
              {loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
              {loading ? "Analyzing" : "Analyze Resume"}
            </button>
          </form>

          {error && (
            <div className="error-box">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
        </aside>

        <section className="results-area">
          {!analysis ? (
            <EmptyState />
          ) : (
            <>
              <div className="score-band">
                <div>
                  <span className="eyebrow">Candidate</span>
                  <h2>{analysis.candidate_name || "Resume Review"}</h2>
                  <p>{analysis.summary}</p>
                  <span className="source-pill">
                    {analysis.analysis_source === "gemini_llm" ? "Gemini LLM report" : "Local NLP fallback"}
                  </span>
                </div>
                <div className={`score-dial ${scoreTone}`} style={{ "--score": `${analysis.score}%` }}>
                  <strong>{analysis.score}</strong>
                  <span>/100</span>
                </div>
              </div>

              <div className="grid two-col">
                <InfoCard icon={<BadgeCheck />} title="Strengths" items={analysis.strengths} />
                <InfoCard icon={<AlertCircle />} title="Gaps" items={analysis.gaps} />
              </div>

              <section className="report-section">
                <header className="section-heading">
                  <span>
                    <Brain size={18} />
                  </span>
                  <div>
                    <h2>LLM Resume Report</h2>
                    <p>{analysis.llm_report}</p>
                  </div>
                </header>
              </section>

              <div className="grid two-col">
                <InfoCard icon={<Sparkles />} title="Recommendations" items={analysis.recommendations} />
                <InfoCard icon={<BriefcaseBusiness />} title="Suitable Roles" items={analysis.suitable_roles} />
              </div>

              <section className="project-section">
                <header className="section-heading">
                  <span>
                    <ClipboardCheck size={18} />
                  </span>
                  <div>
                    <h2>Project Testing</h2>
                    <p>Each project is scored for clarity, tech stack, features, impact, and proof links.</p>
                  </div>
                </header>

                {analysis.project_scores?.length ? (
                  <div className="project-list">
                    {analysis.project_scores.map((project) => (
                      <ProjectCard project={project} key={`${project.title}-${project.score}`} />
                    ))}
                  </div>
                ) : (
                  <p className="muted">No clear project entries were detected.</p>
                )}
              </section>

              <section className="skill-section">
                <SkillGroup title="Extracted Skills" skills={analysis.extracted_skills} />
                <SkillGroup title="Matched Skills" skills={analysis.matched_skills} />
                <SkillGroup title="Missing Skills" skills={analysis.missing_skills} warn />
              </section>
            </>
          )}
        </section>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <FileText size={46} />
      <h2>Upload a resume to begin</h2>
      <p>Your analysis will show scoring, skill extraction, job match, gaps, and practical improvement steps.</p>
    </div>
  );
}

function ProjectCard({ project }) {
  return (
    <article className="project-card">
      <div className="project-topline">
        <div>
          <h3>{project.title}</h3>
          <p>{project.evidence}</p>
        </div>
        <strong>{project.score}/100</strong>
      </div>
      <div className="project-meter" aria-label={`Project score ${project.score} out of 100`}>
        <span style={{ width: `${project.score}%` }} />
      </div>
      <SkillGroup title="Detected Stack" skills={project.detected_skills} />
      <div className="grid two-col compact">
        <InfoCard icon={<BadgeCheck />} title="Project Strengths" items={project.strengths} />
        <InfoCard icon={<AlertCircle />} title="Project Fixes" items={project.improvements} />
      </div>
    </article>
  );
}

function InfoCard({ icon, title, items }) {
  return (
    <article className="info-card">
      <header>
        <span>{icon}</span>
        <h3>{title}</h3>
      </header>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

function SkillGroup({ title, skills, warn = false }) {
  return (
    <div className="skill-group">
      <h3>{title}</h3>
      <div className="chips">
        {skills.length ? (
          skills.map((skill) => (
            <span className={warn ? "chip warn" : "chip"} key={skill}>
              {skill}
            </span>
          ))
        ) : (
          <span className="muted">None detected</span>
        )}
      </div>
    </div>
  );
}

export default App;
