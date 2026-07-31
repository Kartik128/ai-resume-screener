import React, { useState } from 'react';
import {
  X, Sparkles, Star, Briefcase, Building2, GraduationCap,
  Award, MapPin, TrendingUp, CheckCircle2, XCircle, AlertTriangle, Info, Edit2
} from 'lucide-react';
import ScoreOverridePanel from './ScoreOverridePanel';

// ── Helpers ──────────────────────────────────────────────────────────────────

const scoreColor = (score) => {
  if (score >= 85) return { bar: 'bg-emerald-500', text: 'text-emerald-400', ring: 'border-emerald-500/40 bg-emerald-500/10' };
  if (score >= 70) return { bar: 'bg-blue-500',    text: 'text-blue-400',    ring: 'border-blue-500/40 bg-blue-500/10'    };
  if (score >= 50) return { bar: 'bg-amber-500',   text: 'text-amber-400',   ring: 'border-amber-500/40 bg-amber-500/10'  };
  return             { bar: 'bg-rose-500',    text: 'text-rose-400',    ring: 'border-rose-500/40 bg-rose-500/10'    };
};

const fitLabel = (score) => {
  if (score >= 85) return { label: 'Strong Fit',    cls: 'text-emerald-300 bg-emerald-950/60 border-emerald-600/40' };
  if (score >= 70) return { label: 'Good Fit',      cls: 'text-blue-300    bg-blue-950/60    border-blue-600/40'    };
  if (score >= 50) return { label: 'Moderate Fit',  cls: 'text-amber-300  bg-amber-950/60   border-amber-600/40'   };
  return             { label: 'Weak Fit',      cls: 'text-rose-300    bg-rose-950/60    border-rose-600/40'    };
};

// ── Dimension config ─────────────────────────────────────────────────────────

const DIMENSIONS = [
  {
    key: 'mandatory_skills',
    label: 'Mandatory Skills',
    icon: Star,
    iconColor: 'text-blue-400',
    description: 'How well the candidate matches the required technical and domain skills listed in the JD',
  },
  {
    key: 'experience',
    label: 'Experience Depth',
    icon: Briefcase,
    iconColor: 'text-emerald-400',
    description: 'Years of professional experience vs the minimum and maximum experience required for this role',
  },
  {
    key: 'nice_to_have_skills',
    label: 'Preferred / Bonus Skills',
    icon: Sparkles,
    iconColor: 'text-purple-400',
    description: 'Alignment with preferred (nice-to-have) skills that add extra value beyond the baseline requirements',
  },
  {
    key: 'career_stability',
    label: 'Career Stability',
    icon: TrendingUp,
    iconColor: 'text-cyan-400',
    description: "Average tenure per role — frequent job-hopping reduces this score",
  },
  {
    key: 'industry_match',
    label: 'Industry Domain Match',
    icon: Building2,
    iconColor: 'text-amber-400',
    description: "Whether the candidate's past industry experience aligns with this role's sector (e.g. FinTech, Healthcare, SaaS)",
  },
  {
    key: 'education',
    label: 'Education Fit',
    icon: GraduationCap,
    iconColor: 'text-rose-400',
    description: "Candidate's highest degree vs the education requirement specified in the job posting",
  },
  {
    key: 'certifications',
    label: 'Certifications',
    icon: Award,
    iconColor: 'text-yellow-400',
    description: 'Relevant professional certifications that validate domain expertise for this role',
  },
  {
    key: 'location',
    label: 'Location',
    icon: MapPin,
    iconColor: 'text-indigo-400',
    description: "Geographic alignment between the candidate's location and the job's location or remote policy",
  },
];

// ── ScoreBar ─────────────────────────────────────────────────────────────────

function ScoreBar({ score, animated = true }) {
  const c = scoreColor(score);
  return (
    <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ease-out ${c.bar}`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

// ── DimensionRow ─────────────────────────────────────────────────────────────

function DimensionRow({ dim, data, isLast, scoreId, onOverrideApplied }) {
  const c = scoreColor(data.raw_score);
  const Icon = dim.icon;
  const [showOverride, setShowOverride] = useState(false);

  return (
    <div className={`py-4 ${!isLast ? 'border-b border-slate-800/70' : ''}`}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0 mt-0.5">
          <Icon className={`w-4 h-4 ${dim.iconColor}`} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-white">{dim.label}</span>
              <span className="text-[10px] font-bold text-slate-500 bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
                Weight {data.weight_percentage}%
              </span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={`text-sm font-bold ${c.text}`}>{data.raw_score.toFixed(0)}/100</span>
              <span className={`text-[10px] font-semibold ${c.text}`}>
                (+{data.weighted_score.toFixed(1)} pts)
              </span>
              {scoreId && (
                <button
                  onClick={() => setShowOverride(!showOverride)}
                  className="p-1 rounded bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-400 hover:text-white"
                  title="Adjust score manually"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Progress bar */}
          <ScoreBar score={data.raw_score} />

          {/* Reasoning text */}
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">{data.reasoning}</p>

          {/* Tooltip hint */}
          <p className="mt-1 text-[10px] text-slate-600 flex items-center gap-1">
            <Info className="w-3 h-3 shrink-0" />
            {dim.description}
          </p>

          {/* Evidence Citations list */}
          {data.citations && data.citations.length > 0 && (
            <div className="mt-2.5 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] space-y-1.5">
              <span className="font-bold text-slate-400 block uppercase tracking-wider text-[9px] mb-1">🔍 Evidence Citations</span>
              {data.citations.map((cit, idx) => (
                <div key={idx} className="space-y-0.5 border-l-2 border-blue-500/40 pl-2">
                  <div className="flex items-center justify-between text-[10px] text-blue-400">
                    <span className="font-semibold">Required: {cit.required_skill}</span>
                    {cit.matched_candidate_skill && (
                      <span className="text-slate-500">Found: {cit.matched_candidate_skill}</span>
                    )}
                  </div>
                  <p className="text-slate-300 italic">"{cit.evidence_sentence}"</p>
                  {cit.char_start !== null && (
                    <span className="text-[9px] text-slate-500 font-semibold block">Offsets: {cit.char_start} - {cit.char_end}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Recruiter Override Panel */}
          {showOverride && scoreId && (
            <ScoreOverridePanel
              scoreId={scoreId}
              dimensionKey={dim.key}
              dimensionLabel={dim.label}
              currentScore={data.raw_score}
              onOverrideApplied={() => {
                setShowOverride(false);
                onOverrideApplied();
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

import { useEffect } from 'react';

export default function ScoreBreakdownModal({ candidate, onClose }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const bd = candidate?.score_breakdown;
  const overall = candidate?.overall_score ?? 0;
  const fit = fitLabel(overall);
  const oc = scoreColor(overall);

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

  // Sort dimensions by weighted contribution descending for visual impact
  const sortedDims = [...DIMENSIONS].sort((a, b) => {
    const wa = bd?.[a.key]?.weighted_score ?? 0;
    const wb = bd?.[b.key]?.weighted_score ?? 0;
    return wb - wa;
  });

  // Compute total weighted pts for the donut-style breakdown
  const totalWeightedPts = DIMENSIONS.reduce(
    (sum, d) => sum + (bd?.[d.key]?.weighted_score ?? 0), 0
  );

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div
        className="w-full max-w-5xl rounded-2xl border border-purple-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(168,85,247,0.3)] flex flex-col pointer-events-auto"
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          height: '85vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >

        {/* ── Drag-Header ────────────────────────────────────────────── */}
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-purple-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-purple-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center font-bold text-white text-sm shadow-lg">
              {(candidate?.full_name || '?').split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()}
            </div>
            <div>
              <h2 className="font-heading font-bold text-white text-lg leading-tight flex items-center gap-1.5">
                <span className="text-purple-300">AI Ranking Breakdown</span>
                <span className="text-[9px] font-bold bg-purple-950 text-purple-300 border border-purple-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
              </h2>
              <p className="text-xs text-slate-350">{candidate?.full_name} — Score Derivation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* ── Side-by-Side Flex Layout ────────────────────────────────── */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* Left Column: Summary Metrics (35% width) */}
          <div className="w-[35%] border-r border-slate-800/60 p-6 flex flex-col justify-between overflow-y-auto bg-slate-950/20 space-y-4 shrink-0">
            
            <div className="space-y-4">
              {/* Overall Score Wheel Box */}
              <div className="flex items-center gap-4 bg-slate-900/65 p-4 rounded-2xl border border-slate-800">
                <div className={`relative flex items-center justify-center w-16 h-16 rounded-full border-4 ${oc.ring} shrink-0`}>
                  <div className="text-center">
                    <span className={`text-xl font-extrabold font-heading ${oc.text}`}>{overall.toFixed(1)}</span>
                    <span className="block text-[8px] text-slate-500">/100</span>
                  </div>
                </div>
                <div>
                  <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-bold border ${fit.cls}`}>
                    {fit.label}
                  </span>
                  <div className="flex items-center gap-1 mt-1 text-[10px] text-purple-400 font-semibold">
                    <Sparkles className="w-3 h-3" />
                    <span>AI Evaluated</span>
                  </div>
                </div>
              </div>

              {/* Match summary text */}
              {bd?.match_summary && (
                <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-850 text-[11px] text-slate-300 leading-relaxed space-y-2">
                  <span className="font-bold text-slate-405 block uppercase tracking-wider text-[9px]">💡 AI Summary Match</span>
                  <p>{bd.match_summary}</p>
                </div>
              )}
            </div>

            {/* Weights Formula math list */}
            <div className="space-y-2">
              <span className="font-bold text-slate-405 block uppercase tracking-wider text-[9px]">📊 Score Weights Sum</span>
              <div className="grid grid-cols-1 gap-1.5">
                {DIMENSIONS.map(dim => {
                  const score = bd?.[dim.key];
                  if (!score) return null;
                  const c = scoreColor(score.raw_score);
                  return (
                    <div key={dim.key} className="flex justify-between items-center bg-slate-900/40 px-3 py-1 rounded-xl border border-slate-850 text-[10px]">
                      <span className="text-slate-400 font-medium">{dim.label}</span>
                      <span className={`font-semibold ${c.text}`}>
                        {score.weight_percentage}% × {score.raw_score.toFixed(0)} = {score.weighted_score.toFixed(1)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Score Guide Legend */}
            <div className="p-3 bg-slate-900/30 rounded-2xl border border-slate-850 text-[10px] space-y-1.5 shrink-0">
              <span className="font-bold text-slate-500 uppercase tracking-wider block">Score Guide</span>
              <div className="grid grid-cols-2 gap-1.5 font-medium">
                <span className="text-emerald-400">85–100 Excellent</span>
                <span className="text-blue-400">70–84 Good</span>
                <span className="text-amber-400">50–69 Moderate</span>
                <span className="text-rose-400">0–49 Weak</span>
              </div>
            </div>

          </div>

          {/* Right Column: Detailed Dimensions Scrolling Timeline (65% width) */}
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-900/30">
            <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/40 flex justify-between items-center shrink-0">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Evaluation Dimensions — sorted by score impact
              </span>
              <span className="text-[10px] text-slate-500 font-bold">Σ = {totalWeightedPts.toFixed(1)} pts</span>
            </div>
            
            <div className="flex-1 overflow-y-auto px-6 divide-y divide-slate-800/60">
              {sortedDims.map((dim, i) =>
                bd?.[dim.key] ? (
                  <DimensionRow
                    key={dim.key}
                    dim={dim}
                    data={bd[dim.key]}
                    isLast={i === sortedDims.length - 1}
                    scoreId={candidate.score_id}
                    onOverrideApplied={() => {
                      if (typeof onClose === 'function') {
                        onClose();
                      }
                    }}
                  />
                ) : null
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
