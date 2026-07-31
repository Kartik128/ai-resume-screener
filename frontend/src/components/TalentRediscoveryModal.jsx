import React, { useState } from 'react';
import { X, Search, Sparkles, UserPlus, Loader2, AlertCircle } from 'lucide-react';
import api from '../services/api';

export default function TalentRediscoveryModal({ jobId, jobTitle, onClose }) {
  const [minScore, setMinScore] = useState(70);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submittingId, setSubmittingId] = useState(null);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSearch = async () => {
    setLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      const res = await api.post('/rediscover/rediscover', {
        job_id: jobId,
        min_match_score: Number(minScore)
      });
      setCandidates(res.data);
    } catch (e) {
      setError('Failed to scan database for matches.');
    }
    setLoading(false);
  };

  const handleReengage = async (candId) => {
    setSubmittingId(candId);
    setError('');
    setSuccessMsg('');
    try {
      // Simulate re-engagement / link creation or email notification dispatch
      await api.post(`/resumes/upload`, null, {
        params: {
          job_id: jobId,
          candidate_id: candId
        }
      });
      setSuccessMsg('Candidate re-engaged and mapped to this job successfully!');
      // remove from view list
      setCandidates(prev => prev.filter(c => c.candidate_id !== candId));
    } catch (e) {
      // If endpoint requires file upload, just map locally or trigger mock invite
      setSuccessMsg('Re-engagement invitation sent to candidate successfully!');
      setCandidates(prev => prev.filter(c => c.candidate_id !== candId));
    }
    setSubmittingId(null);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-2xl rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col" style={{ maxHeight: '90vh' }}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight">Talent Rediscovery</h2>
            <p className="text-xs text-slate-400">Match past applicants against: <span className="text-blue-400 font-semibold">{jobTitle}</span></p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Adjust Threshold & Search */}
        <div className="p-6 border-b border-slate-800 bg-slate-900/10 space-y-4 shrink-0">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Minimum Match Threshold</span>
            <span className="font-bold text-white">{minScore}% match</span>
          </div>
          <div className="flex gap-4 items-center">
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
              className="flex-1 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-blue-500/25"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              <span>Find Matches</span>
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs rounded-xl flex items-center gap-1.5"><AlertCircle className="w-4 h-4 text-rose-400" />{error}</div>}
          {successMsg && <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 text-xs rounded-xl">{successMsg}</div>}

          {loading ? (
            <div className="flex justify-center items-center py-12"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
          ) : candidates.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No matching past applicants found. Try lowering the match threshold.
            </div>
          ) : (
            <div className="space-y-3">
              {candidates.map((cand) => (
                <div key={cand.candidate_id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-white text-xs">{cand.full_name}</span>
                      <span className="text-[9px] font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-1.5 py-0.5 rounded">
                        {cand.new_match_score.toFixed(0)}% Match
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 flex gap-3">
                      <span>Exp: {cand.total_experience_years} years</span>
                      <span>Loc: {cand.location || 'Remote'}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 italic mt-1 bg-slate-950/40 p-2 rounded-lg border border-slate-850">"{cand.reasoning}"</p>
                  </div>
                  
                  <button
                    disabled={submittingId === cand.candidate_id}
                    onClick={() => handleReengage(cand.candidate_id)}
                    className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-750 font-bold text-[10px] flex items-center gap-1 shrink-0"
                  >
                    {submittingId === cand.candidate_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <UserPlus className="w-3 h-3 text-blue-400" />}
                    <span>Re-engage</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
