import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, AlertTriangle, FileText, Sparkles, MapPin, Briefcase } from 'lucide-react';
import api from '../services/api';

export default function CandidateCard({ candidate, onStatusChange, isSelectedForCompare, onToggleSelectCompare }) {
  const [loading, setLoading] = useState(false);
  const [showCopilotModal, setShowCopilotModal] = useState(false);
  const [copilotData, setCopilotData] = useState({ questions: [], redFlags: null });

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 70) return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  const handleStatus = async (status) => {
    setLoading(true);
    try {
      await api.patch(`/dashboard/application/${candidate.application_id}/status`, { status });
      onStatusChange();
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
      setCopilotData({ questions: qRes.data.questions, redFlags: rRes.data });
    } catch (e) {
      console.error(e);
    }
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
            <h3 className="font-heading font-semibold text-lg text-white leading-tight">{candidate.full_name}</h3>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
              <span className="flex items-center"><Briefcase className="w-3 h-3 mr-1" />{candidate.total_experience_years || 0} Yrs Exp</span>
              <span className="flex items-center"><MapPin className="w-3 h-3 mr-1" />{candidate.location || 'Remote'}</span>
            </div>
          </div>
        </div>

        <div className={`px-3 py-1.5 rounded-xl border font-heading font-bold text-base flex items-center space-x-1.5 ${getScoreColor(candidate.overall_score)}`}>
          <Sparkles className="w-4 h-4" />
          <span>{candidate.overall_score.toFixed(1)}</span>
        </div>
      </div>

      {/* Recruiter AI Summary */}
      <div className="mt-4 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
        <span className="font-semibold text-blue-400">AI Summary: </span>
        {candidate.summary_text || 'Qualified candidate with strong domain experience.'}
      </div>

      {/* Action Controls & Copilot Trigger */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
        <button
          onClick={loadCopilotData}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-purple-400 bg-purple-950/40 hover:bg-purple-900/50 border border-purple-800/40 transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Questions & Flags</span>
        </button>

        <div className="flex items-center space-x-1.5">
          <button
            disabled={loading}
            onClick={() => handleStatus('shortlisted')}
            className={`p-1.5 rounded-lg transition-colors ${
              candidate.status === 'shortlisted' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-emerald-400 hover:bg-emerald-950/40'
            }`}
            title="Shortlist Candidate"
          >
            <CheckCircle2 className="w-4 h-4" />
          </button>
          <button
            disabled={loading}
            onClick={() => handleStatus('maybe')}
            className={`p-1.5 rounded-lg transition-colors ${
              candidate.status === 'maybe' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-amber-400 hover:bg-amber-950/40'
            }`}
            title="Mark Maybe"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
          <button
            disabled={loading}
            onClick={() => handleStatus('rejected')}
            className={`p-1.5 rounded-lg transition-colors ${
              candidate.status === 'rejected' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-rose-400 hover:bg-rose-950/40'
            }`}
            title="Reject Candidate"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* AI Copilot & Questions Modal */}
      {showCopilotModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-panel w-full max-w-2xl p-6 rounded-2xl max-h-[85vh] overflow-y-auto border border-slate-700 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="font-heading font-bold text-lg text-white flex items-center">
                <Sparkles className="w-5 h-5 text-blue-400 mr-2" />
                AI Copilot: {candidate.full_name}
              </h3>
              <button onClick={() => setShowCopilotModal(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {/* Red Flags Section */}
            {copilotData.redFlags && (
              <div className="mt-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Forensic Anomaly & Risk Analysis</h4>
                {copilotData.redFlags.red_flags?.length > 0 ? (
                  <div className="space-y-2">
                    {copilotData.redFlags.red_flags.map((flag, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/40 flex items-start space-x-2.5">
                        <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                        <div className="text-xs">
                          <span className="font-semibold text-rose-300">[{flag.flag_type}] {flag.description}</span>
                          <p className="text-slate-400 mt-0.5">{flag.evidence}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300">
                    No timeline anomalies or forensic red flags detected.
                  </div>
                )}
              </div>
            )}

            {/* Personalized Interview Questions */}
            <div className="mt-6">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Personalized Interview Questions</h4>
              <div className="space-y-3">
                {copilotData.questions.map((q, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-950 text-blue-400 border border-blue-800 mb-1 inline-block">
                      {q.category}
                    </span>
                    <p className="font-semibold text-slate-100 mt-1">{q.question}</p>
                    <p className="text-slate-400 mt-1"><span className="text-slate-500 font-medium">Rationale:</span> {q.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
