import React, { useEffect, useState } from 'react';
import { X, Sliders, RotateCcw, Save, AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import api from '../services/api';

const DIMENSIONS = [
  { key: 'w_mandatory_skills', label: 'Mandatory Skills', color: 'blue', desc: 'Direct alignment with required JD skills' },
  { key: 'w_experience', label: 'Experience Depth', color: 'emerald', desc: 'Years of experience vs required range' },
  { key: 'w_nice_to_have', label: 'Preferred Skills', color: 'purple', desc: 'Nice-to-have / bonus skills alignment' },
  { key: 'w_career_stability', label: 'Career Stability', color: 'cyan', desc: 'Average tenure per role (job-hopping)' },
  { key: 'w_industry_match', label: 'Industry Domain', color: 'amber', desc: 'Sector / domain experience relevance' },
  { key: 'w_education', label: 'Education Fit', color: 'rose', desc: 'Degree level vs JD requirement' },
  { key: 'w_certifications', label: 'Certifications', color: 'yellow', desc: 'Relevant professional certifications' },
  { key: 'w_location', label: 'Location', color: 'indigo', desc: 'Geographic / remote work alignment' },
];

const DEFAULT_WEIGHTS = {
  w_mandatory_skills: 40,
  w_experience: 20,
  w_nice_to_have: 10,
  w_career_stability: 10,
  w_industry_match: 8,
  w_education: 5,
  w_certifications: 4,
  w_location: 3,
};

const colorMap = {
  blue: 'bg-blue-500',
  emerald: 'bg-emerald-500',
  purple: 'bg-purple-500',
  cyan: 'bg-cyan-500',
  amber: 'bg-amber-500',
  rose: 'bg-rose-500',
  yellow: 'bg-yellow-500',
  indigo: 'bg-indigo-500',
};

const textMap = {
  blue: 'text-blue-400',
  emerald: 'text-emerald-400',
  purple: 'text-purple-400',
  cyan: 'text-cyan-400',
  amber: 'text-amber-400',
  rose: 'text-rose-400',
  yellow: 'text-yellow-400',
  indigo: 'text-indigo-400',
};

export default function ScorecardEditorModal({ jobId, jobTitle, onClose, onSaved }) {
  const [weights, setWeights] = useState({ ...DEFAULT_WEIGHTS });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isCustom, setIsCustom] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const total = Object.values(weights).reduce((s, v) => s + Number(v), 0);
  const isValid = Math.abs(total - 100) < 0.5;

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/scorecards/${jobId}`);
        const d = res.data;
        setWeights({
          w_mandatory_skills: d.w_mandatory_skills,
          w_experience: d.w_experience,
          w_nice_to_have: d.w_nice_to_have,
          w_career_stability: d.w_career_stability,
          w_industry_match: d.w_industry_match,
          w_education: d.w_education,
          w_certifications: d.w_certifications,
          w_location: d.w_location,
        });
        setIsCustom(d.is_custom);
      } catch (e) {
        setError('Failed to load scorecard. Using defaults.');
      }
      setLoading(false);
    };
    load();
  }, [jobId]);

  const handleChange = (key, value) => {
    setWeights(prev => ({ ...prev, [key]: Number(value) }));
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    if (!isValid) {
      setError(`Weights must sum to exactly 100%. Current total: ${total.toFixed(1)}%`);
      return;
    }
    setSaving(true);
    try {
      await api.put(`/scorecards/${jobId}`, weights);
      setIsCustom(true);
      setSuccess('Scorecard saved! New weights will apply on next scoring run.');
      onSaved?.();
    } catch (e) {
      setError(e?.response?.data?.detail?.[0]?.msg || 'Failed to save scorecard.');
    }
    setSaving(false);
  };

  const handleReset = async () => {
    try {
      await api.post(`/scorecards/${jobId}/reset`);
      setWeights({ ...DEFAULT_WEIGHTS });
      setIsCustom(false);
      setSuccess('Reset to AI default weights.');
      onSaved?.();
    } catch (e) {
      setError('Reset failed.');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-xl rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col" style={{ maxHeight: '92vh' }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-blue-500 flex items-center justify-center">
              <Sliders className="w-4 h-4 text-white" />
            </div>
            <div>
              <h2 className="font-heading font-bold text-white text-base leading-tight">Scoring Weights Editor</h2>
              <p className="text-xs text-slate-400">{jobTitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isCustom && (
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-lg bg-purple-950/60 text-purple-300 border border-purple-700/40">
                Custom
              </span>
            )}
            <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Total indicator */}
        <div className={`mx-6 mt-4 shrink-0 flex items-center justify-between px-4 py-2.5 rounded-xl border text-sm font-semibold ${
          isValid
            ? 'bg-emerald-950/30 border-emerald-700/40 text-emerald-300'
            : 'bg-rose-950/30 border-rose-700/40 text-rose-300'
        }`}>
          <span className="flex items-center gap-2">
            {isValid ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            Total weight: <strong>{total.toFixed(1)}%</strong>
          </span>
          <span className="text-xs opacity-70">{isValid ? 'Ready to save' : 'Must equal 100%'}</span>
        </div>

        {/* Sliders */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-slate-500 text-sm">Loading scorecard…</div>
          ) : (
            DIMENSIONS.map(dim => {
              const val = weights[dim.key] ?? 0;
              const bar = colorMap[dim.color];
              const txt = textMap[dim.color];
              return (
                <div key={dim.key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className={`text-sm font-semibold ${txt}`}>{dim.label}</span>
                      <p className="text-[10px] text-slate-600">{dim.desc}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={1}
                        value={val}
                        onChange={(e) => handleChange(dim.key, e.target.value)}
                        className="w-14 text-center text-sm font-bold bg-slate-900 border border-slate-700 rounded-lg py-1 text-white focus:border-blue-500 focus:outline-none"
                      />
                      <span className="text-xs text-slate-500">%</span>
                    </div>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={80}
                    step={1}
                    value={val}
                    onChange={(e) => handleChange(dim.key, e.target.value)}
                    className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-800"
                    style={{
                      background: `linear-gradient(to right, var(--tw-gradient-stops))`,
                    }}
                  />
                  {/* Mini bar showing proportion */}
                  <div className="h-1 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${bar}`}
                      style={{ width: `${Math.min((val / 50) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Feedback */}
        {(error || success) && (
          <div className={`mx-6 mb-1 px-3 py-2 rounded-xl text-xs border ${
            error
              ? 'bg-rose-950/30 border-rose-700/40 text-rose-300'
              : 'bg-emerald-950/30 border-emerald-700/40 text-emerald-300'
          }`}>
            {error || success}
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800/80 bg-slate-900/40 rounded-b-2xl flex items-center justify-between shrink-0 gap-3">
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset to Defaults
          </button>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!isValid || saving}
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors shadow-lg shadow-blue-500/20"
            >
              <Save className="w-3.5 h-3.5" />
              {saving ? 'Saving…' : 'Save Scorecard'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
