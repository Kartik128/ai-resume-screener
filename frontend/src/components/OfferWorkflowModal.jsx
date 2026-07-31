import React, { useState } from 'react';
import { X, DollarSign, Send, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function OfferWorkflowModal({ candidateId, candidateName, onClose, onReleased }) {
  const [baseSalary, setBaseSalary] = useState('');
  const [equity, setEquity] = useState('');
  const [releasing, setReleasing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleRelease = async (e) => {
    e.preventDefault();
    if (!baseSalary) return;
    setReleasing(true);
    setError('');
    setSuccess('');
    try {
      await api.post('/offers/release', {
        candidate_id: candidateId,
        job_id: 'bdbd8046-98fb-4cd8-b7d9-621049068f5c', // mock job fallback
        base_salary: Number(baseSalary),
        equity_grants: equity || null
      });
      setSuccess('Compensation offer released and sent for signing successfully!');
      setTimeout(() => {
        onReleased();
        onClose();
      }, 1500);
    } catch (err) {
      setError('Failed to dispatch compensation offer letter package.');
    }
    setReleasing(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-sm rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight">Offer Workflow</h2>
            <p className="text-xs text-slate-400">Release offer package: {candidateName}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <form onSubmit={handleRelease} className="p-6 space-y-4 text-xs">
          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl">{error}</div>}
          {success && <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 rounded-xl">{success}</div>}

          <div>
            <label className="block text-slate-350 font-semibold mb-1">Base Salary (Annual USD) *</label>
            <div className="relative">
              <DollarSign className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="number"
                required
                value={baseSalary}
                onChange={(e) => setBaseSalary(e.target.value)}
                placeholder="120000"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-350 font-semibold mb-1">Equity Grants (e.g. 10,000 Stock Options)</label>
            <input
              type="text"
              value={equity}
              onChange={(e) => setEquity(e.target.value)}
              placeholder="0.05% options, 4-year vest"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={releasing || !baseSalary}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
          >
            {releasing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>Release Compensation Offer</span>
          </button>
        </form>
      </div>
    </div>
  );
}
