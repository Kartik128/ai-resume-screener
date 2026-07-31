import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Users, DollarSign, Plus, RefreshCw, Target, Loader2, AlertTriangle } from 'lucide-react';
import api from '../services/api';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

const QUARTERS = ['Q1-2025', 'Q2-2025', 'Q3-2025', 'Q4-2025', 'Q1-2026', 'Q2-2026', 'Q3-2026', 'Q4-2026'];

function FillRateBar({ value }) {
  const pct = Math.min(100, value);
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-[10px] font-bold w-9 text-right ${pct >= 80 ? 'text-emerald-400' : pct >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>{value}%</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    open: 'bg-blue-950/40 border-blue-800/50 text-blue-300',
    on_track: 'bg-emerald-950/40 border-emerald-800/50 text-emerald-300',
    at_risk: 'bg-amber-950/40 border-amber-800/50 text-amber-300',
    closed: 'bg-slate-800/60 border-slate-700 text-slate-400',
  };
  const labels = { open: '🔵 Open', on_track: '🟢 On Track', at_risk: '🟡 At Risk', closed: '✅ Closed' };
  return (
    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${map[status] || map.open}`}>
      {labels[status] || status}
    </span>
  );
}

export default function WorkforcePlanning() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state
  const [dept, setDept] = useState('');
  const [role, setRole] = useState('');
  const [count, setCount] = useState(1);
  const [quarter, setQuarter] = useState('Q3-2025');
  const [cost, setCost] = useState('');
  const [planStatus, setPlanStatus] = useState('open');

  const loadSummary = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/workforce/summary');
      setSummary(res.data);
    } catch {
      setError('Failed to load workforce planning data.');
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/workforce/plans', {
        department: dept,
        role_title: role,
        planned_count: count,
        target_quarter: quarter,
        estimated_cost_usd: cost ? parseInt(cost) : 0,
        status: planStatus,
      });
      setShowForm(false);
      setDept(''); setRole(''); setCount(1); setCost('');
      await loadSummary();
    } catch {
      setError('Failed to create headcount plan.');
    }
    setSaving(false);
  };

  const fmt = (n) => n?.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }) || '$0';

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-8">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading font-extrabold text-2xl text-white">Workforce Planning</h1>
            <p className="text-slate-400 text-sm mt-1">Headcount forecast, fill rates & cost-per-hire tracking</p>
          </div>
          <div className="flex gap-2">
            <button onClick={loadSummary} className="p-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 hover:text-white transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
            {user?.role !== 'viewer' && (
              <button
                onClick={() => setShowForm(v => !v)}
                className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-sm transition-all shadow-lg shadow-blue-500/25"
              >
                <Plus className="w-4 h-4" />
                Add Headcount Plan
              </button>
            )}
          </div>
        </div>

      {error && <div className="p-3 bg-rose-950/20 border border-rose-800 text-rose-300 rounded-xl flex gap-2"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />{error}</div>}

      {/* Add Plan Form */}
      {showForm && (
        <form onSubmit={handleCreate} className="glass-card p-6 rounded-2xl border border-slate-700/60 space-y-4">
          <h3 className="font-heading font-bold text-white">New Headcount Demand Plan</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Department *</label>
              <input required value={dept} onChange={e => setDept(e.target.value)} placeholder="e.g. Engineering" className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Role Title *</label>
              <input required value={role} onChange={e => setRole(e.target.value)} placeholder="e.g. Senior Backend Engineer" className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Headcount (# of hires)</label>
              <input type="number" min="1" max="500" value={count} onChange={e => setCount(parseInt(e.target.value))} className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Target Quarter *</label>
              <select required value={quarter} onChange={e => setQuarter(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500">
                {QUARTERS.map(q => <option key={q} value={q}>{q}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Est. Cost/Head (USD)</label>
              <input type="number" min="0" value={cost} onChange={e => setCost(e.target.value)} placeholder="120000" className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-slate-400 text-xs font-semibold mb-1">Status</label>
              <select value={planStatus} onChange={e => setPlanStatus(e.target.value)} className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500">
                <option value="open">Open</option>
                <option value="on_track">On Track</option>
                <option value="at_risk">At Risk</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center gap-2 text-sm">
              {saving && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Plan
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-sm">
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>
      ) : summary ? (
        <>
          {/* KPI Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Planned', value: summary.total_planned, icon: Target, color: 'blue' },
              { label: 'Total Hired', value: summary.total_hired, icon: Users, color: 'emerald' },
              { label: 'Overall Fill Rate', value: `${summary.overall_fill_rate}%`, icon: TrendingUp, color: summary.overall_fill_rate >= 70 ? 'emerald' : 'amber' },
              { label: 'Budget Utilised', value: fmt(summary.total_budget_utilised_usd), icon: DollarSign, color: 'purple', sub: `of ${fmt(summary.total_budget_usd)}` },
            ].map(({ label, value, icon: Icon, color, sub }) => (
              <div key={label} className="glass-card p-5 rounded-2xl border border-slate-700/60">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-400 font-semibold">{label}</span>
                  <div className={`p-2 rounded-lg bg-${color}-500/10`}>
                    <Icon className={`w-4 h-4 text-${color}-400`} />
                  </div>
                </div>
                <p className="font-heading font-extrabold text-2xl text-white">{value}</p>
                {sub && <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>}
              </div>
            ))}
          </div>

          {/* Department Breakdown */}
          {summary.by_department.length > 0 && (
            <div className="glass-card p-6 rounded-2xl border border-slate-700/60">
              <h3 className="font-heading font-bold text-white mb-4 text-sm">Fill Rate by Department</h3>
              <div className="space-y-3">
                {[...summary.by_department].sort((a, b) => b.fill_rate - a.fill_rate).map(d => (
                  <div key={d.department} className="flex items-center gap-4">
                    <div className="w-32 shrink-0">
                      <p className="text-sm font-semibold text-slate-200 truncate">{d.department}</p>
                      <p className="text-[10px] text-slate-500">{d.hired}/{d.planned} hired</p>
                    </div>
                    <div className="flex-1"><FillRateBar value={d.fill_rate} /></div>
                    <div className="w-24 text-right">
                      <p className="text-[10px] text-slate-400">{fmt(d.budget_usd)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Plans Table */}
          {summary.plans.length > 0 ? (
            <div className="glass-card rounded-2xl border border-slate-700/60 overflow-hidden">
              <div className="p-5 border-b border-slate-800/80">
                <h3 className="font-heading font-bold text-white text-sm">Headcount Plans ({summary.plans.length})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-900/60">
                    <tr>
                      {['Department', 'Role', 'Quarter', 'Planned', 'Hired', 'Fill Rate', 'Cost/Head', 'Budget Used', 'Status'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {summary.plans.map(p => (
                      <tr key={p.id} className="hover:bg-slate-900/40 transition-colors">
                        <td className="px-4 py-3 text-slate-300 font-semibold">{p.department}</td>
                        <td className="px-4 py-3 text-white font-medium">{p.role_title}</td>
                        <td className="px-4 py-3 text-slate-400">{p.target_quarter}</td>
                        <td className="px-4 py-3 text-slate-300">{p.planned_count}</td>
                        <td className="px-4 py-3 text-slate-300">{p.actual_hired}</td>
                        <td className="px-4 py-3 w-32"><FillRateBar value={p.fill_rate} /></td>
                        <td className="px-4 py-3 text-slate-400">{p.estimated_cost_usd ? fmt(p.estimated_cost_usd) : '—'}</td>
                        <td className="px-4 py-3 text-slate-400">{p.budget_utilised_usd ? fmt(p.budget_utilised_usd) : '—'}</td>
                        <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="glass-card p-12 rounded-2xl border border-slate-700/60 text-center">
              <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 font-semibold">No headcount plans created yet.</p>
              <p className="text-slate-600 text-sm mt-1">Click "Add Headcount Plan" to forecast your hiring demand.</p>
            </div>
          )}
        </>
      ) : null}
      </main>
    </div>
  );
}
