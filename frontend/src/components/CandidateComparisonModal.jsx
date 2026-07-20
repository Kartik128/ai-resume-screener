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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-5xl p-6 rounded-2xl max-h-[90vh] overflow-y-auto border border-slate-700 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <h3 className="font-heading font-bold text-xl text-white flex items-center">
            <Sparkles className="w-5 h-5 text-blue-400 mr-2" />
            Side-by-Side Candidate Comparison
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading AI Comparison Matrix...</div>
        ) : data ? (
          <div className="mt-6 space-y-6">
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
