import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, FunnelChart, Funnel, LabelList } from 'recharts';
import { BarChart3, Users, Clock, Award, TrendingUp } from 'lucide-react';
import api from '../services/api';

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get('/analytics/overview');
        setData(res.data);
      } catch (e) {
        console.error(e);
      }
      setLoading(false);
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <div className="glass-panel p-6 rounded-3xl border border-slate-800">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Recruitment Metrics</span>
          <h1 className="font-heading font-extrabold text-2xl text-white mt-1">HR Analytics & Hiring Funnel</h1>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs">Computing HR Analytics Metrics...</div>
        ) : data ? (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400">Total Applicants</p>
                  <p className="font-heading font-extrabold text-2xl text-white mt-0.5">{data.total_candidates}</p>
                </div>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Award className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400">Avg Candidate Score</p>
                  <p className="font-heading font-extrabold text-2xl text-white mt-0.5">{data.average_candidate_score} / 100</p>
                </div>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400">Time to Hire</p>
                  <p className="font-heading font-extrabold text-2xl text-white mt-0.5">{data.average_time_to_hire_days} Days</p>
                </div>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400">Active Openings</p>
                  <p className="font-heading font-extrabold text-2xl text-white mt-0.5">{data.total_jobs}</p>
                </div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Hiring Funnel Chart */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-800">
                <h3 className="font-heading font-bold text-base text-white mb-4">Hiring Funnel Stage Conversion</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.hiring_funnel} layout="vertical">
                      <XAxis type="number" stroke="#64748b" fontSize={12} />
                      <YAxis dataKey="stage" type="category" stroke="#94a3b8" fontSize={12} width={100} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                      <Bar dataKey="count" fill="#3b82f6" radius={[0, 8, 8, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Skill Gap Analysis Chart */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-800">
                <h3 className="font-heading font-bold text-base text-white mb-4">Skill Gap Analysis (Missing Mandatory Skills)</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.top_skill_gaps}>
                      <XAxis dataKey="skill_name" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#64748b" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                      <Bar dataKey="percentage" fill="#ef4444" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-10 text-center text-rose-400">Failed to load analytics data.</div>
        )}
      </main>
    </div>
  );
}
