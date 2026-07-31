import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, AlertTriangle, Sparkles, MapPin, Briefcase, FileText } from 'lucide-react';
import api from '../services/api';
import ResumeViewerModal from './ResumeViewerModal';
import ScoreBreakdownModal from './ScoreBreakdownModal';
import CandidateTimelineModal from './CandidateTimelineModal';
import IntegrationsModal from './IntegrationsModal';
import QualityOfHireModal from './QualityOfHireModal';
import InterviewIntelligenceModal from './InterviewIntelligenceModal';

import { useAuth } from '../context/AuthContext';

export default function CandidateCard({ candidate, onStatusChange, isSelectedForCompare, onToggleSelectCompare }) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showCopilotModal, setShowCopilotModal] = useState(false);
  const [showResumeViewer, setShowResumeViewer] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);
  const [showIntegrations, setShowIntegrations] = useState(false);
  const [showQoH, setShowQoH] = useState(false);
  const [showIntelModal, setShowIntelModal] = useState(false);
  const [copilotData, setCopilotData] = useState({ questions: [], redFlags: null });
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 70) return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  const handleStatus = async (status) => {
    setLoading(true);
    try {
      await api.patch(`/pipeline/${candidate.application_id}/stage`, { stage: status });
      onStatusChange(candidate.application_id, status);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadCopilotData = async () => {
    setShowCopilotModal(true);
    try {
      const [qRes, rRes] = await Promise.all([
        api.get(`/copilot/interview-questions/${candidate.job_id}/${candidate.candidate_id}`),
        api.get(`/copilot/red-flags/${candidate.job_id}/${candidate.candidate_id}`)
      ]);
      setCopilotData({ questions: qRes.data.questions || [], redFlags: rRes.data });
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    const userQ = chatMessage;
    setChatMessage('');
    setChatHistory((prev) => [...prev, { role: 'user', content: userQ }]);
    setChatLoading(true);
    try {
      const res = await api.post('/copilot/chat', {
        job_id: candidate.job_id,
        candidate_id: candidate.candidate_id,
        question: userQ
      });
      setChatHistory((prev) => [...prev, { role: 'ai', content: res.data.answer }]);
    } catch (err) {
      setChatHistory((prev) => [...prev, { role: 'ai', content: 'Unable to process question right now.' }]);
    }
    setChatLoading(false);
  };

  return (
    <div className={`glass-card p-5 rounded-2xl transition-all hover:border-blue-500/40 relative ${
      isSelectedForCompare ? 'ring-2 ring-blue-500 bg-blue-950/20' : ''
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <input
            type="checkbox"
            checked={isSelectedForCompare}
            onChange={() => onToggleSelectCompare(candidate.candidate_id)}
            className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-blue-600 focus:ring-blue-500 cursor-pointer"
          />
          <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-slate-800 to-slate-700 flex items-center justify-center font-heading font-bold text-white text-lg shadow-inner">
            {candidate.full_name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowResumeViewer(true)}
                className="font-heading font-semibold text-lg text-white leading-tight hover:text-blue-300 transition-colors text-left group flex items-center space-x-1.5"
                title="View Resume"
              >
                <span>{candidate.full_name}</span>
                <FileText className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
              </button>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                AI Verified
              </span>
            </div>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
              <span className="flex items-center"><Briefcase className="w-3.5 h-3.5 mr-1" />{candidate.total_experience_years || 0} Yrs Exp</span>
              <span className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1" />{candidate.location || 'Remote'}</span>
              {candidate.rank_percentile !== undefined && (
                <span className="text-[10px] text-slate-400 bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded font-semibold">
                  Top {Math.max(0.1, 100 - candidate.rank_percentile).toFixed(0)}% Rank
                </span>
              )}
            </div>
            {/* Calibration warnings */}
            {candidate.calibration_flags && candidate.calibration_flags.length > 0 && (
              <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                {candidate.calibration_flags.includes('TIE') && (
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-amber-950/40 text-amber-400 border border-amber-800/40 flex items-center gap-1" title="Candidate's score is within 2 points of nearby candidates">
                    <span>⚠️ Score Tie</span>
                  </span>
                )}
                {candidate.calibration_flags.includes('LOW_EVIDENCE') && (
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-rose-950/40 text-rose-400 border border-rose-800/40 flex items-center gap-1" title="Short resume experience profile. AI match might lack support data.">
                    <span>⚠️ Low Evidence</span>
                  </span>
                )}
                {candidate.calibration_flags.includes('OUTLIER') && (
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-blue-950/40 text-blue-400 border border-blue-800/40 flex items-center gap-1" title="Statistical score outlier compared to company avg candidates list">
                    <span>ℹ️ Score Outlier</span>
                  </span>
                )}
              </div>
            )}

            {/* Duplicate & Assessment badges */}
            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
              {candidate.duplicate_detected && (
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-red-950/40 text-red-400 border border-red-800/40" title="Possible candidate duplicate application found across portal records">
                  ⚠️ Duplicate Detected
                </span>
              )}
              {candidate.assessment_score !== null && candidate.assessment_score !== undefined && (
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-950/40 text-emerald-400 border border-emerald-800/40" title={`Candidate completed lightweight skills validation test. Grade: ${candidate.assessment_score}%`}>
                  🧪 Test Grade: {candidate.assessment_score}%
                </span>
              )}
              {candidate.is_internal && (
                <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-indigo-950/40 text-indigo-400 border border-indigo-800/40" title="Internal Mobility employee applicant candidate profile">
                  💼 Internal Employee
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Score Badge — click to open breakdown */}
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={() => setShowBreakdown(true)}
            className={`px-3 py-1.5 rounded-xl border font-heading font-bold text-base flex items-center space-x-1.5 transition-all hover:scale-105 hover:shadow-lg ${getScoreColor(candidate.overall_score)}`}
            title="View AI Score Breakdown"
          >
            <Sparkles className="w-4 h-4" />
            <span>{candidate.overall_score.toFixed(1)}</span>
          </button>
          <span className="text-[9px] text-slate-600 font-medium">click for breakdown</span>
        </div>
      </div>

      {/* Recruiter AI Summary */}
      <div className="mt-4 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed shadow-inner">
        <div className="flex items-center space-x-1.5 text-blue-400 font-semibold mb-1">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Hiring Copilot Assessment</span>
        </div>
        {candidate.score_breakdown?.match_summary || candidate.summary_text || `AI Evaluation: Candidate presents ${candidate.overall_score.toFixed(0)}% overall suitability alignment with ${candidate.total_experience_years || 0} years of experience.`}
      </div>

      {/* Action Controls & Copilot Trigger */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <button
          onClick={loadCopilotData}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-purple-300 bg-purple-950/60 hover:bg-purple-900/80 border border-purple-700/50 shadow-md transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5 text-purple-400" />
          <span>Ask AI Copilot</span>
        </button>

        <div className="flex items-center space-x-1.5">
          {/* Interview Intelligence Audio Transcript Upload */}
          {user?.role !== 'viewer' && (
            <button
              onClick={() => setShowIntelModal(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-purple-300 hover:text-white bg-purple-950/40 hover:bg-purple-900/60 border border-purple-800/50"
              title="Interview Intelligence — AI transcript analysis"
            >
              🎙️ Intel
            </button>
          )}

          {/* Integrations Communication Button */}
          {user?.role !== 'viewer' && (
            <button
              onClick={() => setShowIntegrations(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-750"
              title="Send Email or Schedule Calendar Invites"
            >
              Invite
            </button>
          )}

          {/* Timeline Link */}
          <button
            onClick={() => setShowTimeline(true)}
            className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-750"
            title="View Pipeline Timeline & Notes"
          >
            Timeline & Notes
          </button>

          {/* Quality-of-Hire Review — shown only for joined candidates */}
          {candidate.status === 'joined' && user?.role !== 'viewer' && (
            <button
              onClick={() => setShowQoH(true)}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-emerald-300 hover:text-white bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/50"
              title="Submit post-hire quality-of-hire review (30/60/90-day feedback)"
            >
              ⭐ QoH Review
            </button>
          )}

          {user?.role !== 'viewer' ? (
            <select
              value={candidate.status}
              disabled={loading}
              onChange={(e) => handleStatus(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg text-xs text-white px-2 py-1.5 font-semibold focus:outline-none focus:border-blue-500"
            >
              <option value="applied">Applied</option>
              <option value="shortlisted">Shortlisted</option>
              <option value="maybe">Maybe</option>
              <option value="interviewed">Interviewed</option>
              <option value="offer_released">Offer Released</option>
              <option value="joined">Joined</option>
              <option value="rejected">Rejected</option>
            </select>
          ) : (
            <span className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-semibold text-slate-400 capitalize">
              {candidate.status}
            </span>
          )}
        </div>
      </div>

      {/* AI Copilot & Interview Questions Modal */}
      {showCopilotModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
          onClick={(e) => e.target === e.currentTarget && setShowCopilotModal(false)}
        >
          <div className="glass-card max-w-2xl w-full p-6 rounded-2xl max-h-[85vh] overflow-y-auto border border-purple-500/30 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-purple-400" />
                <h3 className="font-heading font-semibold text-lg text-white">AI Copilot Analysis: {candidate.full_name}</h3>
              </div>
              <button onClick={() => setShowCopilotModal(false)} className="text-slate-400 hover:text-white text-sm font-bold">✕ Close</button>
            </div>

            {/* Interactive AI Chat Box */}
            <div className="mb-6 p-4 rounded-xl bg-slate-900/90 border border-slate-800">
              <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2 flex items-center space-x-1">
                <Sparkles className="w-3.5 h-3.5 mr-1" /> Ask AI Anything About This Candidate
              </h4>
              <div className="space-y-3 max-h-48 overflow-y-auto mb-3 text-xs">
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`p-2.5 rounded-lg ${msg.role === 'user' ? 'bg-blue-900/40 text-blue-200 text-right ml-8' : 'bg-purple-900/30 text-purple-200 mr-8 border border-purple-800/40'}`}>
                    <span className="font-semibold block text-[10px] text-slate-400 mb-0.5">{msg.role === 'user' ? 'You' : 'AI Hiring Copilot'}</span>
                    {msg.content}
                  </div>
                ))}
              </div>
              <form onSubmit={handleSendChat} className="flex gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="e.g. Compare candidate skills against JD minimum requirements..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500"
                />
                <button disabled={chatLoading} type="submit" className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold">
                  {chatLoading ? 'Asking AI...' : 'Ask AI'}
                </button>
              </form>
            </div>

            {/* Generated Interview Questions */}
            <div className="mb-6">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">AI Recommended Screening Questions</h4>
              <div className="space-y-3">
                {copilotData.questions.length > 0 ? (
                  copilotData.questions.map((q, i) => (
                    <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/90 text-xs">
                      <div className="font-semibold text-blue-300 mb-1">Q{i + 1}: {q.question}</div>
                      <div className="text-slate-400 text-[11px] mb-1"><span className="text-slate-500">Why Ask:</span> {q.rationale}</div>
                      <div className="text-emerald-400/90 text-[11px]"><span className="text-slate-500">Good Answer Signal:</span> {q.expected_answer_signal}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-500 py-4 text-center">Generating candidate-specific questions...</div>
                )}
              </div>
            </div>

            {/* AI Red Flag Anomaly Detection */}
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">AI Anomaly & Risk Detection</h4>
              {copilotData.redFlags ? (
                <div className="space-y-2 text-xs">
                  {copilotData.redFlags.red_flags.length > 0 ? (
                    copilotData.redFlags.red_flags.map((flag, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/40 text-rose-300 flex items-start space-x-2.5">
                        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                        <div>
                          <div className="font-semibold">{flag.flag_type}: {flag.description}</div>
                          <div className="text-[11px] text-rose-400/80 mt-0.5">Evidence: {flag.evidence}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 text-xs flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>No critical timeline anomalies or red flags detected in candidate profile.</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-xs text-slate-500 py-4 text-center">Checking timeline & credentials...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Resume Viewer Modal — opens when name is clicked */}
      {showResumeViewer && candidate.resume_id && (
        <ResumeViewerModal
          resumeId={candidate.resume_id}
          candidateName={candidate.full_name}
          onClose={() => setShowResumeViewer(false)}
        />
      )}

      {/* Fallback: no resume stored yet */}
      {showResumeViewer && !candidate.resume_id && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm"
          onClick={() => setShowResumeViewer(false)}
        >
          <div className="glass-card p-6 rounded-2xl text-center space-y-3 max-w-sm border border-slate-700">
            <FileText className="w-8 h-8 text-slate-500 mx-auto" />
            <p className="text-slate-300 text-sm font-semibold">No resume file linked to this candidate.</p>
            <p className="text-slate-500 text-xs">Resume may have been uploaded without a file (text-only parse).</p>
            <button onClick={() => setShowResumeViewer(false)} className="px-4 py-2 text-xs bg-slate-800 rounded-lg text-slate-300 hover:bg-slate-700">Close</button>
          </div>
        </div>
      )}

      {/* AI Score Breakdown Modal — opens when score badge is clicked */}
      {showBreakdown && (
        <ScoreBreakdownModal
          candidate={candidate}
          onClose={() => {
            setShowBreakdown(false);
            // Refresh rankings list
            onStatusChange(candidate.application_id, candidate.status);
          }}
        />
      )}

      {/* Candidate Activity Timeline & Notes Modal */}
      {showTimeline && (
        <CandidateTimelineModal
          applicationId={candidate.application_id}
          candidateId={candidate.candidate_id}
          candidateName={candidate.full_name}
          onClose={() => setShowTimeline(false)}
        />
      )}

      {/* Email & Calendar scheduler integrations */}
      {showIntegrations && (
        <IntegrationsModal
          applicationId={candidate.application_id}
          candidateId={candidate.candidate_id}
          jobId={candidate.job_id}
          candidateName={candidate.full_name}
          onClose={() => {
            setShowIntegrations(false);
            onStatusChange();
          }}
        />
      )}

      {/* Quality-of-Hire post-hire review */}
      {showQoH && (
        <QualityOfHireModal
          candidateId={candidate.candidate_id}
          candidateName={candidate.full_name}
          jobId={candidate.job_id}
          onClose={() => setShowQoH(false)}
        />
      )}

      {/* Interview Intelligence Audio Transcript Analysis */}
      {showIntelModal && (
        <InterviewIntelligenceModal
          candidateId={candidate.candidate_id}
          jobId={candidate.job_id}
          candidateName={candidate.full_name}
          onClose={() => setShowIntelModal(false)}
        />
      )}
    </div>
  );
}
