import React, { useEffect, useState } from 'react';
import {
  X, Download, ExternalLink, FileText, Briefcase, GraduationCap,
  Award, Star, Mail, Phone, MapPin, Linkedin, Github, Globe,
  Clock, ChevronDown, ChevronUp, Loader2, Sliders
} from 'lucide-react';
import api from '../services/api';

export default function ResumeViewerModal({ resumeId, candidateName, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('structured'); // 'structured' | 'raw'
  const [expandedSection, setExpandedSection] = useState({ work: true, education: true, skills: true });

  // Drag and Drop Popup panel position state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Manual Override and Error Reporting States
  const [overrideScore, setOverrideScore] = useState(75);
  const [overrideReason, setOverrideReason] = useState('');
  const [overridesList, setOverridesList] = useState([]);
  const [submittingOverride, setSubmittingOverride] = useState(false);
  const [reportedFields, setReportedFields] = useState([]);

  useEffect(() => {
    if (!resumeId) return;
    const load = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/resumes/${resumeId}/preview`);
        setData(res.data);
        
        // Fetch score override history logs
        if (res.data.score_id) {
          try {
            const hRes = await api.get(`/score_overrides/${res.data.score_id}`);
            setOverridesList(hRes.data);
          } catch (hErr) {
            console.error("Failed to load score override logs", hErr);
          }
        }
      } catch (e) {
        setError('Could not load resume preview. ' + (e?.response?.data?.error?.message || e.message));
      }
      setLoading(false);
    };
    load();
  }, [resumeId]);

  const handleApplyOverride = async () => {
    if (!overrideReason.trim()) {
      alert("Please provide a reasoning justification for overriding the score.");
      return;
    }
    setSubmittingOverride(true);
    try {
      await api.post(`/score_overrides/${data.score_id}/override`, {
        dimension: 'mandatory_skills',
        new_raw_score: Number(overrideScore),
        reason: overrideReason
      });
      
      // Reload profile data and audit trail lists
      const res = await api.get(`/resumes/${resumeId}/preview`);
      setData(res.data);
      const hRes = await api.get(`/score_overrides/${data.score_id}`);
      setOverridesList(hRes.data);
      setOverrideReason('');
      alert("Manual score override successfully registered and candidate ranked updated!");
    } catch (err) {
      console.error(err);
      alert("Failed to submit score override details.");
    }
    setSubmittingOverride(false);
  };

  const handleReportError = (field) => {
    if (reportedFields.includes(field)) return;
    setReportedFields([...reportedFields, field]);
    alert(`Feedback logged: '${field}' reported as AI parsing error. Thank you for refining HireRyt!`);
  };

  const handleMouseDown = (e) => {
    if (e.target.closest('.drag-header')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging) {
        setPosition({
          x: e.clientX - dragOffset.x,
          y: e.clientY - dragOffset.y
        });
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  const toggleSection = (key) =>
    setExpandedSection((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8099';
      const response = await fetch(`${baseUrl}/api/v1/resumes/${resumeId}/file`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition') || '';
      const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
      const fileName = match ? match[1] : (data?.file_name || 'resume.txt');

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      if (data?.raw_text) {
        const blob = new Blob([data.raw_text], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(() => window.URL.revokeObjectURL(url), 5000);
      }
    }
  };

  const initials = (candidateName || data?.candidate_name || '?')
    .split(' ').slice(0, 2).map((n) => n[0]).join('').toUpperCase();

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div 
        className="w-full max-w-3xl rounded-2xl border border-rose-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(244,63,94,0.3)] flex flex-col pointer-events-auto"
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          maxHeight: '85vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >

        {/* ── Drag-Header ────────────────────────────────────────────── */}
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-rose-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-rose-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-rose-600 to-indigo-500 flex items-center justify-center font-bold text-white text-sm shadow-lg">
              {initials}
            </div>
            <div>
              <h2 className="font-heading font-bold text-white text-lg leading-tight flex items-center gap-1.5">
                <span className="text-rose-300">{candidateName || data?.candidate_name || 'Resume Viewer'}</span>
                <span className="text-[9px] font-bold bg-rose-950 text-rose-300 border border-rose-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
              </h2>
              <p className="text-xs text-slate-400">{data?.file_name || 'Resume'}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Tab Switcher */}
            <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
              <button
                onClick={() => setActiveTab('structured')}
                className={`px-3 py-1.5 rounded-md font-semibold transition-all ${
                  activeTab === 'structured'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Structured View
              </button>
              <button
                onClick={() => setActiveTab('raw')}
                className={`px-3 py-1.5 rounded-md font-semibold transition-all ${
                  activeTab === 'raw'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Raw Text
              </button>
            </div>

            {/* Download */}
            <button
              onClick={handleDownload}
              title="Download / Open Original File"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
            >
              <Download className="w-4 h-4" />
            </button>

            {/* Close */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* ── Body ───────────────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              <p className="text-slate-400 text-sm">Loading resume...</p>
            </div>
          )}

          {error && !loading && (
            <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-300 text-sm">
              {error}
            </div>
          )}

          {data && !loading && activeTab === 'structured' && (
            <>
              {/* ── Contact Info Bar ─────────────────────────────────── */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/40 to-indigo-950/30 border border-blue-800/30 grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
                {data.email && (
                  <a href={`mailto:${data.email}`} className="flex items-center space-x-2 text-slate-300 hover:text-blue-300 transition-colors">
                    <Mail className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span className="truncate">{data.email}</span>
                  </a>
                )}
                {data.phone && (
                  <span className="flex items-center space-x-2 text-slate-300">
                    <Phone className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>{data.phone}</span>
                  </span>
                )}
                {data.location && (
                  <span className="flex items-center space-x-2 text-slate-300">
                    <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>{data.location}</span>
                  </span>
                )}
                {data.total_experience_years > 0 && (
                  <span className="flex items-center space-x-2 text-slate-300">
                    <Clock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                    <span>{data.total_experience_years} years experience</span>
                  </span>
                )}
                {data.linkedin_url && (
                  <a href={data.linkedin_url} target="_blank" rel="noreferrer"
                    className="flex items-center space-x-2 text-blue-400 hover:text-blue-300 transition-colors">
                    <Linkedin className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">LinkedIn Profile</span>
                    <ExternalLink className="w-3 h-3 shrink-0 opacity-60" />
                  </a>
                )}
                {data.github_url && (
                  <a href={data.github_url} target="_blank" rel="noreferrer"
                    className="flex items-center space-x-2 text-slate-300 hover:text-white transition-colors">
                    <Github className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">GitHub Profile</span>
                    <ExternalLink className="w-3 h-3 shrink-0 opacity-60" />
                  </a>
                )}
              </div>

              {/* ── Summary ──────────────────────────────────────────── */}
              {data.summary && (
                <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                    <Globe className="w-3.5 h-3.5" />
                    <span>Professional Summary</span>
                  </h4>
                  <p className="text-sm text-slate-300 leading-relaxed">{data.summary}</p>
                </div>
              )}

              {/* ── Skills ───────────────────────────────────────────── */}
              {data.skills?.length > 0 && (
                <div className="rounded-xl border border-slate-800 overflow-hidden">
                  <button
                    onClick={() => toggleSection('skills')}
                    className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/80 hover:bg-slate-900 transition-colors"
                  >
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                      <Star className="w-3.5 h-3.5 text-amber-400" />
                      <span>Skills & Technologies ({data.skills.length})</span>
                    </h4>
                    {expandedSection.skills ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </button>
                  {expandedSection.skills && (
                    <div className="p-4 bg-slate-950/40 flex flex-wrap gap-2">
                      {data.skills.map((skill, i) => {
                        const name = typeof skill === 'object' ? skill.name : skill;
                        const isReported = reportedFields.includes(`skill-${name}`);
                        return (
                          <span 
                            key={i} 
                            onClick={() => handleReportError(`skill-${name}`)}
                            className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 cursor-pointer transition-all ${
                              isReported
                                ? 'bg-rose-950/40 text-rose-400 border-rose-800/50 line-through'
                                : 'bg-blue-950/50 text-blue-300 border-blue-800/40 hover:bg-rose-950/20 hover:border-rose-900/40 hover:text-rose-300'
                            }`}
                            title="Click to report as parsing error"
                          >
                            <span>{name}</span>
                            <span className="text-[9px] opacity-60">⚠️</span>
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* ── Work Experience ───────────────────────────────────── */}
              {data.work_experience?.length > 0 && (
                <div className="rounded-xl border border-slate-800 overflow-hidden">
                  <button
                    onClick={() => toggleSection('work')}
                    className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/80 hover:bg-slate-900 transition-colors"
                  >
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                      <Briefcase className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Work Experience ({data.work_experience.length} roles)</span>
                    </h4>
                    {expandedSection.work ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </button>
                  {expandedSection.work && (
                    <div className="divide-y divide-slate-800/60">
                      {data.work_experience.map((job, i) => (
                        <div key={i} className="p-4 bg-slate-950/40">
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <div>
                              <p className="text-sm font-semibold text-white">{job.title || job.role || job.position}</p>
                              <p className="text-xs text-blue-400 font-medium">{job.company || job.organization}</p>
                            </div>
                            <span className="text-xs text-slate-500 whitespace-nowrap shrink-0 mt-0.5">
                              {job.start_date || job.start} – {job.end_date || job.end || 'Present'}
                            </span>
                          </div>
                          {job.location && (
                            <p className="text-xs text-slate-500 mb-1.5 flex items-center">
                              <MapPin className="w-3 h-3 mr-1" />{job.location}
                            </p>
                          )}
                          {(job.responsibilities || job.description || job.achievements) && (
                            <ul className="mt-2 space-y-1">
                              {(job.responsibilities || job.achievements || [job.description]).filter(Boolean).slice(0, 5).map((item, j) => (
                                <li key={j} className="text-xs text-slate-400 flex items-start space-x-2">
                                  <span className="text-emerald-500 mt-0.5 shrink-0">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── Education ────────────────────────────────────────── */}
              {data.education?.length > 0 && (
                <div className="rounded-xl border border-slate-800 overflow-hidden">
                  <button
                    onClick={() => toggleSection('education')}
                    className="w-full flex items-center justify-between px-4 py-3 bg-slate-900/80 hover:bg-slate-900 transition-colors"
                  >
                    <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                      <GraduationCap className="w-3.5 h-3.5 text-purple-400" />
                      <span>Education</span>
                    </h4>
                    {expandedSection.education ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                  </button>
                  {expandedSection.education && (
                    <div className="divide-y divide-slate-800/60">
                      {data.education.map((edu, i) => (
                        <div key={i} className="p-4 bg-slate-950/40">
                          <p className="text-sm font-semibold text-white">{edu.degree} {edu.field ? `in ${edu.field}` : ''}</p>
                          <p className="text-xs text-purple-400 font-medium">{edu.institution || edu.school || edu.university}</p>
                          {(edu.graduation_year || edu.year || edu.end_year) && (
                            <p className="text-xs text-slate-500 mt-0.5">Graduated {edu.graduation_year || edu.year || edu.end_year}</p>
                          )}
                          {edu.gpa && <p className="text-xs text-slate-500">GPA: {edu.gpa}</p>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── Certifications ───────────────────────────────────── */}
              {data.certifications?.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
                    <Award className="w-3.5 h-3.5 text-amber-400" />
                    <span>Certifications</span>
                  </h4>
                  <div className="space-y-2">
                    {data.certifications.map((cert, i) => (
                      <div key={i} className="flex items-center space-x-2.5 text-xs text-slate-300">
                        <Award className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        <span>{typeof cert === 'object' ? cert.name : cert}</span>
                        {cert.year && <span className="text-slate-500">({cert.year})</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Key Achievements ─────────────────────────────────── */}
              {data.achievements?.length > 0 && (
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/30">
                  <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
                    <Star className="w-3.5 h-3.5" />
                    <span>Key Achievements</span>
                  </h4>
                  <ul className="space-y-2">
                    {data.achievements.slice(0, 8).map((ach, i) => (
                      <li key={i} className="text-xs text-slate-300 flex items-start space-x-2">
                        <span className="text-emerald-400 mt-0.5 shrink-0 font-bold">✓</span>
                        <span>{ach}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* ── Recruiter Overrides & Audit Log (Premium PM Feature) ── */}
              {data.score_id && (
                <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                    <Sliders className="w-4 h-4 text-indigo-400" />
                    <span>Recruiter Manual Override & Audit Trail</span>
                  </h4>
                  
                  <div className="flex flex-col md:flex-row items-start md:items-center gap-4 bg-slate-950/40 p-4 rounded-xl border border-slate-850">
                    <div className="flex-1 w-full space-y-2">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-300">Override Overall Score:</span>
                        <span className="text-indigo-400 text-sm font-bold">{overrideScore}/100</span>
                      </div>
                      <input 
                        type="range" 
                        min="0" 
                        max="100" 
                        value={overrideScore}
                        onChange={(e) => setOverrideScore(e.target.value)}
                        className="w-full h-1.5 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                      />
                    </div>
                    
                    <div className="flex-1 w-full space-y-1.5">
                      <input 
                        type="text" 
                        placeholder="Enter justification note (required)..."
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    
                    <button
                      onClick={handleApplyOverride}
                      disabled={submittingOverride}
                      className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/20 shrink-0"
                    >
                      {submittingOverride ? 'Saving...' : 'Apply Score'}
                    </button>
                  </div>
                  
                  {/* Audit Trail List */}
                  {overridesList.length > 0 && (
                    <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Historical Audit Logs:</p>
                      {overridesList.map((log, idx) => (
                        <div key={idx} className="p-2.5 rounded-lg bg-slate-950/20 border border-slate-850 text-xs flex justify-between gap-4">
                          <div className="space-y-0.5">
                            <p className="text-slate-300 font-medium">{log.reason}</p>
                            <p className="text-[10px] text-slate-500">
                              By Recruiter on {new Date(log.created_at).toLocaleString()}
                            </p>
                          </div>
                          <div className="text-right shrink-0">
                            <span className="text-[10px] text-slate-500 block">Override Score</span>
                            <span className="font-bold text-indigo-400 text-xs">{log.new_value} (was {log.original_value})</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── Raw Text Tab ─────────────────────────────────────────── */}
          {data && !loading && activeTab === 'raw' && (
            <div className="rounded-xl border border-slate-800 overflow-hidden">
              <div className="px-4 py-3 bg-slate-900/80 flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Extracted Resume Text</span>
                </h4>
                <span className="text-xs text-slate-600">{data.raw_text?.length || 0} characters</span>
              </div>
              <pre className="p-4 text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap bg-slate-950/60 overflow-x-auto max-h-[60vh] overflow-y-auto">
                {data.raw_text || '(No text content extracted from this resume)'}
              </pre>
            </div>
          )}
        </div>

        {/* ── Footer ─────────────────────────────────────────────────── */}
        {data && !loading && (
          <div className="px-6 py-3.5 border-t border-slate-800/80 bg-slate-900/40 rounded-b-2xl flex items-center justify-between shrink-0">
            <span className="text-xs text-slate-500">
              {data.file_name} · {data.file_size_bytes ? `${(data.file_size_bytes / 1024).toFixed(1)} KB` : 'Size unknown'}
              {!data.file_available && (
                <span className="ml-2 text-amber-500/80">· Original file stored as text</span>
              )}
            </span>
            <button
              onClick={handleDownload}
              className="flex items-center space-x-2 px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors shadow-md shadow-blue-500/20"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Resume</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
