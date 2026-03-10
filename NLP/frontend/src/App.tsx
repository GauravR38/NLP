import React, { useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";

type AnalyzeResult = {
  ats_breakdown: any;
  section_scores: any[];
  jd_skill_rankings: any[];
  impact_breakdown: any;
  skill_gaps: any[];
  resume_skills: string[];
  rewrite_suggestions: { original: string; improved: string }[];
};

const API_BASE = "http://localhost:8000";

const App: React.FC = () => {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [requiredSkillsText, setRequiredSkillsText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setError("Please upload a PDF resume.");
      return;
    }
    if (!jobDescription.trim()) {
      setError("Please paste the job description.");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);
    formData.append("required_skills_text", requiredSkillsText);

    try {
      const res = await axios.post<AnalyzeResult>(`${API_BASE}/analyze`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setResult(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Analysis failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>ATS-Aware Resume Intelligence</h1>
        <p>
          Upload your resume, paste a job description, and get ATS, section-wise, and impact insights
          with intelligent rewrite suggestions.
        </p>
      </header>

      <section className="card input-card">
        <div className="input-grid">
          <div>
            <h2>1. Upload Resume (PDF)</h2>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
            />
          </div>
          <div>
            <h2>2. Job Description</h2>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the full job description here..."
            />
          </div>
        </div>
        <div className="skills-input">
          <h3>3. Required Skills (optional)</h3>
          <textarea
            value={requiredSkillsText}
            onChange={(e) => setRequiredSkillsText(e.target.value)}
            placeholder="Comma or newline separated skills. If left blank, skills are inferred from the job description."
          />
        </div>

        <div className="actions">
          <motion.button
            className="primary-button"
            whileHover={{ scale: 1.03, boxShadow: "0 12px 30px rgba(0,0,0,0.25)" }}
            whileTap={{ scale: 0.97 }}
            animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
            transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Analyze Resume"}
          </motion.button>
          {error && <p className="error-text">{error}</p>}
        </div>
      </section>

      {result && (
        <section className="results">
          <div className="card">
            <h2>ATS Overview</h2>
            <div className="metrics-row">
              <Metric label="ATS Score" value={`${result.ats_breakdown.overall_score}/100`} />
              <Metric label="Semantic Similarity" value={`${result.ats_breakdown.semantic_similarity}%`} />
              <Metric label="Skill Match" value={`${result.ats_breakdown.skill_match_pct}%`} />
              <Metric label="Keyword Relevance" value={`${result.ats_breakdown.keyword_relevance}%`} />
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2>Section-wise ATS</h2>
              {result.section_scores.length === 0 && <p>No clear sections detected.</p>}
              {result.section_scores.map((sec, idx) => (
                <div key={idx} className="section-score">
                  <h3>{sec.name}</h3>
                  <div className="metrics-row">
                    <Metric label="Section ATS" value={`${sec.overall_section_score}/100`} />
                    <Metric label="Semantic" value={`${sec.semantic_similarity}%`} />
                    <Metric label="Skill Match" value={`${sec.skill_match_pct}%`} />
                    <Metric label="Keywords" value={`${sec.keyword_relevance}%`} />
                  </div>
                  <Progress value={sec.overall_section_score} />
                </div>
              ))}
            </div>

            <div className="card">
              <h2>Resume Impact</h2>
              <Metric label="Impact Score" value={`${result.impact_breakdown.overall_impact_score}/100`} />
              <Progress value={result.impact_breakdown.overall_impact_score} />
              <div className="metrics-row compact">
                <Metric label="Action verbs" value={`${result.impact_breakdown.action_verb_density}%`} />
                <Metric
                  label="Quantified bullets"
                  value={`${result.impact_breakdown.quantified_achievement_density}%`}
                />
                <Metric label="Tech bullets" value={`${result.impact_breakdown.technical_skill_density}%`} />
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2>Critical JD Skills</h2>
              {result.jd_skill_rankings.map((item, idx) => {
                const present = result.resume_skills
                  .map((s) => s.toLowerCase())
                  .includes(String(item.skill).toLowerCase());
                return (
                  <div key={idx} className="jd-skill">
                    <strong>{item.skill}</strong>{" "}
                    <span className="tag">{Math.round(item.importance * 100)}% importance</span>
                    {present ? <span className="tag success">In resume</span> : <span className="tag danger">Missing</span>}
                    <p>
                      Mentions in JD: <strong>{item.frequency}</strong>
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="card">
              <h2>Skill Gaps</h2>
              {result.skill_gaps.length === 0 && <p>No significant skill gaps detected.</p>}
              {result.skill_gaps.map((gap, idx) => (
                <div key={idx} className="skill-gap">
                  <strong>{gap.skill}</strong>{" "}
                  <span className="tag">{Math.round(gap.importance * 100)}% importance</span>
                  <p>{gap.recommendation}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2>Rewrite Suggestions</h2>
            {result.rewrite_suggestions.length === 0 && <p>No obvious weak bullets detected.</p>}
            {result.rewrite_suggestions.map((rw, idx) => (
              <details key={idx} className="rewrite-block">
                <summary>Suggestion {idx + 1}</summary>
                <div className="rewrite-content">
                  <div>
                    <h4>Original</h4>
                    <p>{rw.original}</p>
                  </div>
                  <div>
                    <h4>Improved</h4>
                    <p>{rw.improved}</p>
                  </div>
                </div>
              </details>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="metric">
    <span className="metric-label">{label}</span>
    <span className="metric-value">{value}</span>
  </div>
);

const Progress: React.FC<{ value: number }> = ({ value }) => (
  <div className="progress">
    <div className="progress-bar" style={{ width: `${Math.min(value, 100)}%` }} />
  </div>
);

export default App;

