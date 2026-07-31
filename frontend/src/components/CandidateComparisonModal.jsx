import React, { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '../services/api';

export default function CandidateComparisonModal({ jobId, candidateIds, onClose }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchComparison = async () => {
      try {
        const res = await api.post('/dashboard/compare', {
          job_id: jobId,
          candidate_ids: candidateIds,
        });
        setData(res.data);
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchComparison();
  }, [jobId, candidateIds]);

  const handleDownloadPdf = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/exports/compare?job_id=${jobId}&candidate_ids=${candidateIds.join(',')}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comparison_report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.error(e);
    }
  };

  // Drag and Drop Popup panel position state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

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

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div 
        className="w-full max-w-5xl rounded-2xl border border-amber-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(245,158,11,0.3)] flex flex-col pointer-events-auto" 
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          maxHeight: '85vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-amber-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-amber-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <h3 className="font-heading font-bold text-base text-white flex items-center gap-1.5">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <span className="text-amber-300">Side-by-Side Candidate Comparison</span>
            <span className="text-[9px] font-bold bg-amber-950 text-amber-300 border border-amber-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
          </h3>
          <div className="flex items-center space-x-2">
            <button 
              onClick={handleDownloadPdf}
              className="px-3 py-1.5 rounded-lg border border-blue-500/40 bg-blue-950/30 hover:bg-blue-950/50 text-blue-300 text-[10px] font-bold flex items-center space-x-1 transition-all"
            >
              <span>Download PDF</span>
            </button>
            <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">✕</button>
          </div>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading AI Comparison Matrix...</div>
        ) : data ? (
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Top Recommendation Box */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/60 to-purple-950/60 border border-blue-500/30 flex items-start space-x-3">
              <Sparkles className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-bold text-blue-300 uppercase tracking-wider">AI Recommended Winner</span>
                <p className="text-slate-200 mt-1 text-sm font-medium">{data.recommendation_reasoning}</p>
              </div>
            </div>

            {/* Matrix Comparison Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="p-3 text-slate-400 font-semibold">Criteria</th>
                    {data.columns.map((col) => (
                      <th
                        key={col.candidate_id}
                        className={`p-3 font-bold text-sm text-center ${
                          col.candidate_id === data.recommended_top_candidate_id ? 'text-blue-400 bg-blue-950/30' : 'text-white'
                        }`}
                      >
                        {col.full_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Overall Score</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-center font-heading font-bold text-base text-blue-400">
                        {col.overall_score.toFixed(1)} / 100
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Mandatory Skills Match</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-center font-semibold text-emerald-400">
                        {col.mandatory_skills_score.toFixed(0)}%
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Total Experience</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-center text-slate-300">
                        {col.total_experience_years} Years
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Skills Present</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-center text-slate-400">
                        {col.mandatory_skills_present.join(', ') || 'None'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">AI Match Confidence</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-center">
                        <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                          (col.confidence_score || 85.0) >= 80 ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                          (col.confidence_score || 85.0) >= 60 ? 'bg-amber-950 text-amber-400 border border-amber-800' :
                          'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}>
                          {(col.confidence_score || 85.0).toFixed(0)}%
                        </span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Hiring Risk Alerts</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className="p-3 text-left max-w-xs">
                        <div className="space-y-1.5">
                          {col.risks && col.risks.length > 0 ? (
                            col.risks.map((r, idx) => (
                              <div key={idx} className={`p-1.5 rounded text-[10px] leading-normal flex items-start space-x-1 ${
                                r.includes("No major risk") 
                                  ? 'bg-emerald-950/20 text-emerald-400 border border-emerald-900/40' 
                                  : 'bg-rose-950/25 text-rose-300 border border-rose-900/30'
                              }`}>
                                <span className="mt-0.5 shrink-0">⚠️</span>
                                <span>{r}</span>
                              </div>
                            ))
                          ) : (
                            <span className="text-slate-500 text-[10px]">No risk evaluations calculated.</span>
                          )}
                        </div>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-3 font-semibold text-slate-300">Risk Score</td>
                    {data.columns.map((col) => (
                      <td key={col.candidate_id} className={`p-3 text-center font-bold ${col.risk_score > 30 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {col.risk_score}%
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="py-10 text-center text-rose-400">Failed to load comparison data.</div>
        )}
      </div>
    </div>
  );
}
