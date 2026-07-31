import React, { useState, useEffect } from 'react';
import { X, AlertCircle, Loader2, History } from 'lucide-react';
import api from '../services/api';

export default function ScoreOverridePanel({ scoreId, dimensionKey, dimensionLabel, currentScore, onOverrideApplied }) {
  const [newScore, setNewScore] = useState(currentScore);
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchHistory = async () => {
    try {
      const res = await api.get(`/scores/${scoreId}/audit`);
      setHistory(res.data.filter(item => item.dimension === dimensionKey));
    } catch (e) {
      console.error(e);
    }
    setLoadingHistory(false);
  };

  useEffect(() => {
    if (scoreId) {
      fetchHistory();
    }
  }, [scoreId, dimensionKey]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newScore === currentScore) {
      setError('Please choose a different score value.');
      return;
    }
    if (reason.trim().length < 5) {
      setError('Please provide a descriptive reason (at least 5 characters).');
      return;
    }
    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await api.patch(`/scores/${scoreId}/override`, {
        dimension: dimensionKey,
        new_raw_score: Number(newScore),
        reason: reason.trim()
      });
      setSuccess('Score overridden successfully!');
      setReason('');
      fetchHistory();
      onOverrideApplied();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit score override.');
    }
    setSubmitting(false);
  };

  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-4 text-xs mt-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <span className="font-bold text-slate-300">Recruiter Score Override: {dimensionLabel}</span>
        <span className="text-[10px] text-slate-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">Manual Override</span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1">
            <label className="block text-slate-400 mb-1">Adjust Score (0 - 100)</label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={newScore}
                onChange={(e) => setNewScore(Number(e.target.value))}
                className="flex-1 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
              />
              <span className="font-bold text-white text-sm shrink-0 w-8 text-right">{newScore}</span>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-slate-400 mb-1">Reason for override *</label>
          <input
            type="text"
            placeholder="e.g. verified certifications offline, strong github demo shown in screening call"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={submitting}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
          />
        </div>

        {error && <div className="text-rose-400 flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5" />{error}</div>}
        {success && <div className="text-emerald-400 font-medium">{success}</div>}

        <button
          type="submit"
          disabled={submitting || newScore === currentScore}
          className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg font-bold flex items-center justify-center gap-1.5"
        >
          {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          <span>Apply Manual Score</span>
        </button>
      </form>

      {/* Override History / Audit Log */}
      <div className="space-y-2 pt-2 border-t border-slate-800">
        <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
          <History className="w-3 h-3" />
          <span>Adjustment Audit Trail</span>
        </div>
        {loadingHistory ? (
          <div className="py-2 text-center text-slate-600">Loading audit log…</div>
        ) : history.length === 0 ? (
          <div className="text-slate-600 text-[10px]">No overrides applied yet. Original AI score active.</div>
        ) : (
          <div className="space-y-1.5 max-h-24 overflow-y-auto">
            {history.map((h) => (
              <div key={h.id} className="p-2 rounded bg-slate-950 border border-slate-900">
                <div className="flex items-center justify-between text-[10px] text-slate-500 mb-0.5">
                  <span>{h.overridden_by_name}</span>
                  <span>{new Date(h.created_at).toLocaleDateString()}</span>
                </div>
                <div className="text-[11px] text-slate-350">
                  Adjusted: <span className="font-semibold text-rose-400">{h.original_value.toFixed(0)}</span> → <span className="font-semibold text-emerald-400">{h.new_value.toFixed(0)}</span>
                </div>
                <p className="text-[10px] text-slate-500 italic mt-0.5">"{h.reason}"</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
