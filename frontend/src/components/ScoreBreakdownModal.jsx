import React, { useState } from 'react';
import { X, Sparkles, Star, Briefcase, Building2, GraduationCap, Award, MapPin, TrendingUp, Edit2 } from 'lucide-react';
import ScoreOverridePanel from './ScoreOverridePanel';

const scoreColor = (score) => {
  if (score >= 85) return { bar: 'bg-emerald-500', text: 'text-emerald-400', ring: 'border-emerald-500/30 bg-emerald-500/5', bg: 'bg-emerald-950/30' };
  if (score >= 70) return { bar: 'bg-indigo-500',  text: 'text-indigo-400',  ring: 'border-indigo-500/30 bg-indigo-500/5',   bg: 'bg-indigo-950/30'  };
  if (score >= 50) return { bar: 'bg-amber-500',   text: 'text-amber-400',   ring: 'border-amber-500/30 bg-amber-500/5',    bg: 'bg-amber-950/30'   };
  return             { bar: 'bg-rose-500',    text: 'text-rose-400',    ring: 'border-rose-500/30 bg-rose-500/5',      bg: 'bg-rose-950/30'    };
};

const DIMENSIONS = [
  { key: 'mandatory_skills',   label: 'Mandatory Skills',    icon: Star,          color: 'text-blue-400' },
  { key: 'experience',         label: 'Experience Depth',    icon: Briefcase,     color: 'text-emerald-400' },
  { key: 'nice_to_have_skills', label: 'Bonus Skills',        icon: Sparkles,      color: 'text-purple-400' },
  { key: 'career_stability',   label: 'Stability',           icon: TrendingUp,    color: 'text-cyan-400' },
  { key: 'industry_match',     label: 'Industry Domain',     icon: Building2,     color: 'text-amber-400' },
  { key: 'education',          label: 'Education Fit',       icon: GraduationCap, color: 'text-rose-400' },
  { key: 'certifications',     label: 'Certifications',      icon: Award,         color: 'text-yellow-400' },
  { key: 'location',           label: 'Location Match',      icon: MapPin,        color: 'text-indigo-400' },
];

export default function ScoreBreakdownModal({ candidate, onClose }) {
  const bd = candidate?.score_breakdown;
  const overall = candidate?.overall_score ?? 0;
  const oc = scoreColor(overall);
  const [activeOverrideDim, setActiveOverrideDim] = useState(null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-xl rounded-3xl border border-slate-800 bg-slate-900 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800 shrink-0 bg-slate-950/35">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-white text-base shadow-inner ${oc.bg} border border-slate-800`}>
              {overall.toFixed(0)}
            </div>
            <div>
              <h2 className="font-heading font-bold text-white text-base leading-tight">
                {candidate?.full_name}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">AI Ranking Score Breakdown</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* AI Match Summary */}
          {bd?.match_summary && (
            <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800/80 text-xs text-slate-300 leading-relaxed italic relative">
              <span className="not-italic font-bold text-slate-500 uppercase tracking-wider text-[9px] block mb-1.5 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>AI Fit Evaluation</span>
              </span>
              "{bd.match_summary}"
            </div>
          )}

          {/* List of dimensions */}
          <div className="space-y-4">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Scoring Components</h3>
            <div className="space-y-3.5">
              {DIMENSIONS.map((dim) => {
                const scoreData = bd?.[dim.key];
                if (!scoreData) return null;
                const sc = scoreColor(scoreData.raw_score);
                const Icon = dim.icon;
                const isOverriding = activeOverrideDim === dim.key;

                return (
                  <div key={dim.key} className="p-3.5 rounded-2xl bg-slate-950/30 border border-slate-800/60 hover:border-slate-800 transition-all">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0">
                          <Icon className={`w-3.5 h-3.5 ${dim.color}`} />
                        </div>
                        <div className="min-w-0">
                          <span className="text-xs font-semibold text-white block truncate">{dim.label}</span>
                          <span className="text-[9px] text-slate-500 font-medium">Weight: {scoreData.weight_percentage}%</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2.5 shrink-0">
                        <span className={`text-xs font-bold ${sc.text}`}>{scoreData.raw_score.toFixed(0)}/100</span>
                        {candidate.score_id && (
                          <button
                            onClick={() => setActiveOverrideDim(isOverriding ? null : dim.key)}
                            className={`p-1 rounded-lg border transition-all ${
                              isOverriding
                                ? 'bg-indigo-600 border-indigo-500 text-white'
                                : 'bg-slate-900 border-slate-800 text-slate-450 hover:text-white'
                            }`}
                            title="Override score"
                          >
                            <Edit2 className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-1.5 rounded-full bg-slate-900 overflow-hidden mt-3">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ease-out ${sc.bar}`}
                        style={{ width: `${scoreData.raw_score}%` }}
                      />
                    </div>

                    {/* Reasoning sentence */}
                    <p className="mt-2 text-[11px] text-slate-400 leading-normal">{scoreData.reasoning}</p>

                    {/* Citations Snippets (shortened) */}
                    {scoreData.citations && scoreData.citations.length > 0 && (
                      <div className="mt-2 pl-2 border-l border-slate-800 text-[10px] text-slate-500 space-y-1">
                        {scoreData.citations.slice(0, 2).map((cit, idx) => (
                          <div key={idx} className="italic">
                            - "{cit.evidence_sentence.slice(0, 100)}{cit.evidence_sentence.length > 100 ? '...' : ''}"
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Override Panel */}
                    {isOverriding && candidate.score_id && (
                      <div className="mt-3 border-t border-slate-900 pt-3">
                        <ScoreOverridePanel
                          scoreId={candidate.score_id}
                          dimensionKey={dim.key}
                          dimensionLabel={dim.label}
                          currentScore={scoreData.raw_score}
                          onOverrideApplied={() => {
                            setActiveOverrideDim(null);
                            if (typeof onClose === 'function') onClose();
                          }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
