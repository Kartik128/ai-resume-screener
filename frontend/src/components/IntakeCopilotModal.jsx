import React, { useState } from 'react';
import { X, Sparkles, Wand2, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function IntakeCopilotModal({ onClose, onWeightsSuggested }) {
  const [notes, setNotes] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!notes.trim()) return;
    setAnalyzing(true);
    setError('');
    try {
      const res = await api.post('/intake/analyze', { notes });
      setAnalysisResult(res.data);
    } catch (err) {
      setError('Failed to analyze intake conversation. Ensure text formatting is correct.');
    }
    setAnalyzing(false);
  };

  const applyWeights = () => {
    if (!analysisResult) return;
    onWeightsSuggested(analysisResult.suggested_weights);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-xl rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col" style={{ maxHeight: '85vh' }}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
            <div>
              <h2 className="font-heading font-bold text-white text-base leading-tight">Hiring Manager Intake Copilot</h2>
              <p className="text-xs text-slate-400">Generate scorecards and calibration weights profiles from intake chats</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs">
          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl">{error}</div>}

          {!analysisResult ? (
            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-slate-350 font-semibold mb-1">Paste Intake Discussion / Role Script *</label>
                <textarea
                  rows={8}
                  required
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Hiring Manager: We need a senior backend engineer. They must have deep experience architecting high-scale Python backends. We care a lot about candidate hands-on experience, so we should weight experience higher than formal degrees..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
                />
              </div>

              <button
                type="submit"
                disabled={analyzing || !notes.trim()}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-indigo-500/25"
              >
                {analyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
                <span>Analyze Intake Discussion</span>
              </button>
            </form>
          ) : (
            <div className="space-y-5">
              <div className="p-3.5 rounded-xl bg-indigo-950/15 border border-indigo-900/30 text-indigo-200 leading-relaxed">
                <span className="font-bold block mb-1">AI Copilot Analysis Summary</span>
                {analysisResult.summary}
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Weight allocations */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
                  <span className="font-bold text-slate-300 block border-b border-slate-800 pb-1.5">Suggested Weights Profile</span>
                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Experience Weight:</span>
                      <span className="text-white font-bold">{analysisResult.suggested_weights.experience_weight}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Skills Weight:</span>
                      <span className="text-white font-bold">{analysisResult.suggested_weights.skills_weight}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Education Weight:</span>
                      <span className="text-white font-bold">{analysisResult.suggested_weights.education_weight}%</span>
                    </div>
                  </div>
                </div>

                {/* Key Skills */}
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
                  <span className="font-bold text-slate-300 block border-b border-slate-800 pb-1.5">Identified Mandatory Skills</span>
                  <div className="flex flex-wrap gap-1">
                    {analysisResult.suggested_skills.map((s, i) => (
                      <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] text-slate-300">{s}</span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Calibration Rules */}
              <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-2">
                <span className="font-bold text-slate-300 block">AI Scorecard Calibration Rules</span>
                <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-slate-400">
                  {analysisResult.suggested_scorecard_rules.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setAnalysisResult(null)}
                  className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl border border-slate-700 transition-colors"
                >
                  Analyze New Intake
                </button>
                <button
                  type="button"
                  onClick={applyWeights}
                  className="flex-1 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:opacity-95 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition-all"
                >
                  Apply Suggested Weights
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
