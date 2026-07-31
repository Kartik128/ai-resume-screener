import React, { useState, useEffect } from 'react';
import { X, Star, TrendingUp, Users, BookOpen, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '../services/api';

const PERIODS = [
  { value: '30_day', label: '30-Day Check-in' },
  { value: '60_day', label: '60-Day Check-in' },
  { value: '90_day', label: '90-Day Check-in' },
  { value: '180_day', label: '180-Day Check-in' },
];

const RISK_OPTIONS = [
  { value: 'low', label: '🟢 Low Risk', cls: 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300' },
  { value: 'medium', label: '🟡 Medium Risk', cls: 'bg-amber-950/30 border-amber-800/50 text-amber-300' },
  { value: 'high', label: '🔴 High Risk', cls: 'bg-rose-950/30 border-rose-800/50 text-rose-300' },
];

function RatingSlider({ label, icon: Icon, value, onChange, color = 'blue' }) {
  const colorMap = {
    blue: 'accent-blue-500',
    emerald: 'accent-emerald-500',
    purple: 'accent-purple-500',
  };
  return (
    <div>
      <div className="flex justify-between items-center mb-1.5">
        <label className="text-slate-300 font-semibold flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5 text-slate-400" />
          {label}
        </label>
        <span className={`text-sm font-extrabold ${value >= 8 ? 'text-emerald-400' : value >= 5 ? 'text-amber-400' : 'text-rose-400'}`}>
          {value}/10
        </span>
      </div>
      <input
        type="range"
        min="1" max="10"
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className={`w-full h-2 rounded-full cursor-pointer ${colorMap[color]}`}
      />
      <div className="flex justify-between text-[9px] text-slate-600 mt-1">
        <span>Poor</span><span>Average</span><span>Excellent</span>
      </div>
    </div>
  );
}

export default function QualityOfHireModal({ candidateId, candidateName, jobId, onClose }) {
  const [period, setPeriod] = useState('30_day');
  const [performance, setPerformance] = useState(7);
  const [cultureFit, setCultureFit] = useState(7);
  const [skillsMatch, setSkillsMatch] = useState(7);
  const [retentionRisk, setRetentionRisk] = useState('low');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [pastReviews, setPastReviews] = useState([]);
  const [loadingPast, setLoadingPast] = useState(true);

  useEffect(() => {
    api.get(`/quality-of-hire/candidate/${candidateId}`)
      .then(res => setPastReviews(res.data))
      .catch(() => {})
      .finally(() => setLoadingPast(false));
  }, [candidateId]);

  const composite = Math.round(((performance + cultureFit + skillsMatch) / 3) * 10) / 10;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const res = await api.post('/quality-of-hire/submit', {
        candidate_id: candidateId,
        job_id: jobId,
        review_period: period,
        performance_rating: performance,
        culture_fit_rating: cultureFit,
        skills_match_rating: skillsMatch,
        retention_risk: retentionRisk,
        notes: notes || null,
      });
      setPastReviews(prev => [res.data, ...prev]);
      setSuccess(`${PERIODS.find(p => p.value === period)?.label} review submitted! Composite score: ${composite}/10`);
      setNotes('');
    } catch {
      setError('Failed to submit quality-of-hire review. Please try again.');
    }
    setSubmitting(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-lg rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col" style={{ maxHeight: '92vh' }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight">Quality-of-Hire Review</h2>
            <p className="text-xs text-slate-400">Post-hire feedback loop — {candidateName}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs">

          {/* Composite score preview */}
          <div className={`p-4 rounded-xl border text-center ${composite >= 8 ? 'bg-emerald-950/20 border-emerald-800/40' : composite >= 5 ? 'bg-amber-950/20 border-amber-800/40' : 'bg-rose-950/20 border-rose-800/40'}`}>
            <p className="text-slate-400 text-[10px] uppercase tracking-wider font-semibold mb-1">Live Composite Score</p>
            <p className={`font-heading font-extrabold text-3xl ${composite >= 8 ? 'text-emerald-400' : composite >= 5 ? 'text-amber-400' : 'text-rose-400'}`}>{composite}<span className="text-slate-500 text-sm font-normal">/10</span></p>
          </div>

          {/* Alerts */}
          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl">{error}</div>}
          {success && <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 rounded-xl flex items-start gap-2"><CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />{success}</div>}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Check-in Period */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">Review Period</label>
              <div className="grid grid-cols-2 gap-2">
                {PERIODS.map(p => (
                  <button
                    key={p.value} type="button"
                    onClick={() => setPeriod(p.value)}
                    className={`py-2 rounded-lg text-[11px] font-bold border transition-all ${period === p.value ? 'bg-blue-600 border-blue-500 text-white' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'}`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Rating Sliders */}
            <RatingSlider label="Job Performance" icon={TrendingUp} value={performance} onChange={setPerformance} color="blue" />
            <RatingSlider label="Culture Fit" icon={Users} value={cultureFit} onChange={setCultureFit} color="emerald" />
            <RatingSlider label="Skills Match (vs AI score)" icon={BookOpen} value={skillsMatch} onChange={setSkillsMatch} color="purple" />

            {/* Retention Risk */}
            <div>
              <label className="block text-slate-400 font-semibold mb-2">Retention Risk</label>
              <div className="flex gap-2">
                {RISK_OPTIONS.map(r => (
                  <button
                    key={r.value} type="button"
                    onClick={() => setRetentionRisk(r.value)}
                    className={`flex-1 py-2 rounded-lg text-[10px] font-bold border transition-all ${retentionRisk === r.value ? r.cls : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-300'}`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="block text-slate-400 font-semibold mb-1">Manager Notes (optional)</label>
              <textarea
                rows={3}
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Describe specific areas of strength or improvement since onboarding..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Star className="w-4 h-4" />}
              <span>Submit Review</span>
            </button>
          </form>

          {/* Past reviews */}
          {!loadingPast && pastReviews.length > 0 && (
            <div className="border-t border-slate-800 pt-4 space-y-2">
              <h4 className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Previous Reviews ({pastReviews.length})</h4>
              {pastReviews.map(r => (
                <div key={r.id} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-300 text-[11px]">{PERIODS.find(p => p.value === r.review_period)?.label || r.review_period}</span>
                    <span className={`text-[11px] font-extrabold ${r.composite_score >= 8 ? 'text-emerald-400' : r.composite_score >= 5 ? 'text-amber-400' : 'text-rose-400'}`}>{r.composite_score}/10</span>
                  </div>
                  <div className="flex gap-3 text-[10px] text-slate-400">
                    <span>Perf: <strong>{r.performance_rating}</strong></span>
                    <span>Culture: <strong>{r.culture_fit_rating}</strong></span>
                    <span>Skills: <strong>{r.skills_match_rating}</strong></span>
                    <span className={`font-semibold ${r.retention_risk === 'high' ? 'text-rose-400' : r.retention_risk === 'medium' ? 'text-amber-400' : 'text-emerald-400'}`}>{r.retention_risk} risk</span>
                  </div>
                  {r.notes && <p className="text-[10px] text-slate-500 italic">{r.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
