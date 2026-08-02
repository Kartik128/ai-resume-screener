import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, FunnelChart, Funnel, LabelList } from 'recharts';
import { BarChart3, Users, Clock, Award, TrendingUp, Sparkles, Send, Loader2, MessageSquare } from 'lucide-react';
import api from '../services/api';

import DashboardLayout from '../components/DashboardLayout';

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Natural Language Analytics
  const [nlQuestion, setNlQuestion] = useState('');
  const [nlLoading, setNlLoading] = useState(false);
  const [nlAnswer, setNlAnswer] = useState(null);
  const [nlError, setNlError] = useState('');
  const [nlHistory, setNlHistory] = useState([]);

  const SUGGESTED_QUESTIONS = [
    'Why are engineering roles taking so long?',
    'What skills are we missing most?',
    'How is our hiring funnel performing?',
    'What is our average candidate score by department?',
  ];

  const handleNlAsk = async (question) => {
    const q = question || nlQuestion;
    if (!q.trim()) return;
    setNlLoading(true);
    setNlError('');
    setNlQuestion('');
    try {
      const res = await api.post('/analytics/ask', { question: q });
      setNlHistory(prev => [...prev, { type: 'user', text: q }, { type: 'assistant', data: res.data }]);
    } catch {
      setNlError('Could not process your question. Please try again.');
    }
    setNlLoading(false);
  };

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

  const handleFunnelClick = (entry) => {
    if (entry && entry.stage) {
      // Map stages like "Shortlisted", "Rejected" to filters
      const stageFilter = entry.stage.toLowerCase() === 'all candidates' ? '' : entry.stage.toLowerCase();
      navigate(`/dashboard?status=${stageFilter}`);
    }
  };

  const handleBarClick = (entry) => {
    if (entry && entry.skill_name) {
      navigate(`/dashboard?search=${encodeURIComponent(entry.skill_name)}`);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 shadow-premium">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Recruitment Metrics</span>
          <h1 className="font-heading font-extrabold text-2xl text-white mt-1">HR Analytics & Hiring Funnel</h1>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs">Computing HR Analytics Metrics...</div>
        ) : data ? (
          <div className="space-y-6">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                    <Users className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">Total Applicants</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.total_candidates > 0 ? data.total_candidates : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: SQL Candidates Table count mapped to company_id.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Award className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">Avg Candidate Score</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.total_candidates > 0 ? `${data.average_candidate_score} / 100` : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: Arithmetic mean of all matched candidate scorecard scores.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                    <Clock className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">Time to Hire</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.average_time_to_hire_days > 0 ? `${data.average_time_to_hire_days} Days` : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: Mean elapsed days from intake start date to shortlist.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">Active Openings</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.total_jobs > 0 ? data.total_jobs : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: Total active jobs count associated with your tenant.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-pink-500/10 border border-pink-500/30 flex items-center justify-center text-pink-400" title="Proportion of candidate scores accepted without overrides">
                    <BarChart3 className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">AI Agreement Rate</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.total_candidates > 0 && data.recruiter_ai_agreement_rate > 0 ? `${data.recruiter_ai_agreement_rate}%` : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: Accepted scores without recruiter override actions.
                </p>
              </div>

              <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400" title="Candidate Experience Net Promoter Score">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400">Candidate NPS</p>
                    <p className="font-heading font-extrabold text-2xl text-white mt-0.5">
                      {data.candidate_experience_nps !== 0 ? `${data.candidate_experience_nps > 0 ? '+' : ''}${data.candidate_experience_nps}` : 'Not enough data yet'}
                    </p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 pt-1 border-t border-slate-850">
                  Source: Experience Net Promoter surveys parsed on candidate exit.
                </p>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Hiring Funnel Chart */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-800">
                <h3 className="font-heading font-bold text-base text-white mb-4">Hiring Funnel Stage Conversion</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <FunnelChart>
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                      <Funnel
                        dataKey="count"
                        data={data.hiring_funnel.map(f => ({ ...f, name: f.stage }))}
                        isAnimationActive
                        onClick={handleFunnelClick}
                        className="cursor-pointer"
                      >
                        <LabelList position="right" fill="#94a3b8" stroke="none" dataKey="name" fontSize={11} />
                      </Funnel>
                    </FunnelChart>
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
                      <Bar 
                        dataKey="percentage" 
                        fill="#ef4444" 
                        radius={[8, 8, 0, 0]} 
                        onClick={handleBarClick}
                        className="cursor-pointer"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-10 text-center text-rose-400">Failed to load analytics data.</div>
        )}

        {/* ── Natural Language Analytics ── */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-5">
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-xl bg-purple-500/10">
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="font-heading font-bold text-white text-base">Ask Your Hiring Data</h2>
              <p className="text-xs text-slate-400">Type any question in plain English — get instant data-backed insights</p>
            </div>
          </div>

          {/* Suggested chips */}
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUESTIONS.map(q => (
              <button
                key={q}
                onClick={() => handleNlAsk(q)}
                className="px-3 py-1.5 rounded-full text-xs font-medium border border-purple-800/50 bg-purple-950/30 text-purple-300 hover:bg-purple-900/50 hover:text-white transition-all"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input bar */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <MessageSquare className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={nlQuestion}
                onChange={e => setNlQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleNlAsk()}
                placeholder="e.g. Why are analyst roles taking 45 days to fill?"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
            <button
              onClick={() => handleNlAsk()}
              disabled={nlLoading || !nlQuestion.trim()}
              className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center gap-1.5 transition-all shadow-lg shadow-purple-500/20"
            >
              {nlLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Ask
            </button>
          </div>

          {nlError && <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/40 text-rose-300 text-sm">{nlError}</div>}

          {/* Chat thread */}
          {nlHistory.length > 0 && (
            <div className="space-y-4 max-h-[500px] overflow-y-auto p-2 border border-slate-800/80 rounded-2xl bg-slate-950/40">
              {nlHistory.map((msg, index) => (
                <div key={index} className={`flex flex-col ${msg.type === 'user' ? 'items-end' : 'items-start'}`}>
                  {msg.type === 'user' ? (
                    <div className="bg-purple-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[80%] text-sm font-semibold shadow-md">
                      {msg.text}
                    </div>
                  ) : (
                    <div className="p-5 rounded-2xl rounded-tl-none bg-purple-950/20 border border-purple-800/30 space-y-4 w-full max-w-[90%] shadow-lg">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
                            {msg.data.category?.replace(/_/g, ' ')}
                          </span>
                          <h3 className="text-white font-bold text-base mt-0.5">{msg.data.headline}</h3>
                        </div>
                      </div>

                      {/* Data points */}
                      {msg.data.data_points?.length > 0 && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          {msg.data.data_points.map((dp, i) => (
                            <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                              <p className="text-[10px] text-slate-400 font-semibold mb-1">{dp.label}</p>
                              <p className="text-white font-bold text-sm">{dp.value}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Insight */}
                      {msg.data.insight && (
                        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">💡 Insight</p>
                          <p className="text-slate-300 text-sm leading-relaxed">{msg.data.insight}</p>
                        </div>
                      )}

                      {/* Follow-ups */}
                      {msg.data.suggested_followups?.length > 0 && (
                        <div className="pt-2">
                          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Suggested follow-ups</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.data.suggested_followups.map((f, i) => (
                              <button
                                key={i}
                                onClick={() => handleNlAsk(f)}
                                className="px-3 py-1 rounded-full text-[11px] border border-slate-700 bg-slate-900 text-slate-300 hover:text-white hover:border-purple-600 transition-colors"
                              >
                                {f}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
