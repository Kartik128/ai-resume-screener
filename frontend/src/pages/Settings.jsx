import React, { useState, useEffect, useCallback } from 'react';
import Navbar from '../components/Navbar';
import {
  Shield, Trash2, RefreshCw, AlertTriangle, CheckCircle2,
  Clock, Database, FileText, Loader2, ChevronRight, Lock,
  UserPlus, Mail, Key
} from 'lucide-react';
import api from '../services/api';
import DashboardLayout from '../components/DashboardLayout';

function StatCard({ label, value, sub, icon: Icon, color = 'blue' }) {
  const colMap = {
    blue: 'text-blue-400 bg-blue-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    rose: 'text-rose-400 bg-rose-500/10',
    emerald: 'text-emerald-400 bg-emerald-500/10',
  };
  return (
    <div className="glass-card p-5 rounded-2xl border border-slate-700/60">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-slate-400 font-semibold">{label}</span>
        <div className={`p-2 rounded-lg ${colMap[color]}`}>
          <Icon className={`w-4 h-4 ${colMap[color].split(' ')[0]}`} />
        </div>
      </div>
      <p className="font-heading font-extrabold text-2xl text-white">{value}</p>
      {sub && <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();
  const [retentionData, setRetentionData] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [loadingRetention, setLoadingRetention] = useState(true);
  const [loadingAudit, setLoadingAudit] = useState(true);

  // GDPR erase
  const [eraseId, setEraseId] = useState('');
  const [erasing, setErasing] = useState(false);
  const [eraseResult, setEraseResult] = useState(null);
  const [eraseError, setEraseError] = useState('');
  const [confirmErase, setConfirmErase] = useState(false);

  // Teammates panel states
  const [teammates, setTeammates] = useState([]);
  const [loadingTeammates, setLoadingTeammates] = useState(true);
  const [inviteForm, setInviteForm] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'recruiter'
  });
  const [inviteError, setInviteError] = useState('');
  const [inviteSuccess, setInviteSuccess] = useState('');
  const [inviting, setInviting] = useState(false);

  // Outreach Campaign States
  const [campaigns, setCampaigns] = useState([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState(true);
  const [activeSettingsTab, setActiveSettingsTab] = useState('general'); // 'general' | 'campaigns' | 'nps'
  const [campaignForm, setCampaignForm] = useState({
    trigger_stage: 'screening',
    channel: 'email',
    subject: 'Next steps for your application',
    body: 'Hi {candidate_name},\n\nWe have updated your application status to {stage}...'
  });
  const [campaignError, setCampaignError] = useState('');
  const [campaignSuccess, setCampaignSuccess] = useState('');

  // Candidate experience NPS states
  const [npsData, setNpsData] = useState(null);
  const [loadingNps, setLoadingNps] = useState(true);

  const loadRetention = useCallback(async () => {
    setLoadingRetention(true);
    try {
      const res = await api.get('/governance/data-retention/summary');
      setRetentionData(res.data);
    } catch { }
    setLoadingRetention(false);
  }, []);

  const loadAudit = useCallback(async () => {
    setLoadingAudit(true);
    try {
      const res = await api.get('/governance/audit-log');
      setAuditLog(res.data || []);
    } catch { }
    setLoadingAudit(false);
  }, []);

  const loadTeammates = useCallback(async () => {
    setLoadingTeammates(true);
    try {
      const res = await api.get('/users/');
      setTeammates(res.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoadingTeammates(false);
  }, []);

  const loadCampaigns = useCallback(async () => {
    setLoadingCampaigns(true);
    try {
      const res = await api.get('/campaigns/');
      setCampaigns(res.data || []);
    } catch (e) {
      console.error(e);
    }
    setLoadingCampaigns(false);
  }, []);

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setCampaignError('');
    setCampaignSuccess('');
    try {
      await api.post('/campaigns/', campaignForm);
      setCampaignSuccess('Outreach trigger template added successfully!');
      setCampaignForm({
        trigger_stage: 'screening',
        channel: 'email',
        subject: 'Next steps for your application',
        body: 'Hi {candidate_name},\n\nWe have updated your application status to {stage}...'
      });
      await loadCampaigns();
    } catch {
      setCampaignError('Failed to create campaign template.');
    }
  };

  const handleDeleteCampaign = async (id) => {
    try {
      await api.delete(`/campaigns/${id}`);
      await loadCampaigns();
    } catch {
      setCampaignError('Failed to remove outreach trigger template.');
    }
  };

  const loadNps = useCallback(async () => {
    setLoadingNps(true);
    try {
      const res = await api.get('/experience/summary');
      setNpsData(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoadingNps(false);
  }, []);

  useEffect(() => {
    loadRetention();
    loadAudit();
    loadTeammates();
    loadCampaigns();
    loadNps();
  }, [loadRetention, loadAudit, loadTeammates, loadCampaigns, loadNps]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteForm.email || !inviteForm.full_name || !inviteForm.password) {
      setInviteError('Please fill in all fields.');
      return;
    }
    setInviting(true);
    setInviteError('');
    setInviteSuccess('');
    try {
      // Get current user's company_id dynamically
      const me = await api.get('/auth/me');
      const company_id = me.data.company_id;

      await api.post('/users/', {
        email: inviteForm.email,
        full_name: inviteForm.full_name,
        password: inviteForm.password,
        role: inviteForm.role,
        company_id: company_id
      });

      setInviteSuccess(`Successfully created user ${inviteForm.full_name} (${inviteForm.role})`);
      setInviteForm({
        email: '',
        full_name: '',
        password: '',
        role: 'recruiter'
      });
      await loadTeammates();
    } catch (err) {
      setInviteError(err.response?.data?.message || err.response?.data?.detail || 'Failed to create teammate.');
    }
    setInviting(false);
  };

  const handleErase = async () => {
    if (!eraseId.trim()) return;
    setErasing(true);
    setEraseResult(null);
    setEraseError('');
    try {
      const res = await api.post(`/governance/gdpr/erase/${eraseId.trim()}`);
      setEraseResult(res.data);
      setEraseId('');
      setConfirmErase(false);
      await loadRetention();
    } catch (e) {
      setEraseError(e?.response?.data?.detail || 'Erasure failed. Check candidate ID and admin permissions.');
    }
    setErasing(false);
  };

  const fmtTime = (ts) => ts ? new Date(ts).toLocaleString() : '—';

  if (user?.role !== 'admin') {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center p-6 min-h-[60vh]">
          <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center max-w-md space-y-4 shadow-premium">
            <Lock className="w-12 h-12 text-rose-500 mx-auto" />
            <h2 className="font-heading font-extrabold text-xl text-white">Access Denied</h2>
            <p className="text-slate-400 text-sm leading-relaxed">
              This settings console contains critical GDPR audit logs and data deletion utilities. Only users with **Organization Owner / Admin** privileges are permitted to view this section.
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-800/30">
            <Shield className="w-5 h-5 text-rose-400" />
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-2xl text-white">Governance & Compliance</h1>
            <p className="text-slate-400 text-sm">GDPR right-to-erasure, data retention policies, and audit trail</p>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-800 gap-4 py-1.5 shrink-0">
          <button
            onClick={() => setActiveSettingsTab('general')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeSettingsTab === 'general' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>General settings</span>
          </button>
          <button
            onClick={() => setActiveSettingsTab('campaigns')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeSettingsTab === 'campaigns' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Outreach Campaigns</span>
          </button>
          <button
            onClick={() => { setActiveSettingsTab('nps'); loadNps(); }}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeSettingsTab === 'nps' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Candidate Experience (NPS)</span>
          </button>
        </div>        {activeSettingsTab === 'general' ? (
          <>
            {/* Data Retention Summary */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-blue-400" />
                  <h2 className="font-heading font-bold text-white">Data Retention Overview</h2>
                </div>
                <button onClick={loadRetention} className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {loadingRetention ? (
                <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
              ) : retentionData ? (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard label="Total Candidates" value={retentionData.total_candidates} icon={Database} color="blue" />
                    <StatCard label="> 90 Days Old" value={retentionData.older_than_90_days} sub="Review recommended" icon={Clock} color="amber" />
                    <StatCard label="> 180 Days Old" value={retentionData.older_than_180_days} sub="Archive candidates" icon={Clock} color="amber" />
                    <StatCard label="> 365 Days Old" value={retentionData.older_than_365_days} sub="Erasure eligible" icon={AlertTriangle} color="rose" />
                  </div>
                  <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-800/30 flex items-start gap-3">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-amber-300 text-sm font-semibold">Policy Recommendation</p>
                      <p className="text-amber-400/80 text-xs mt-0.5">{retentionData.policy_recommendation}</p>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-slate-500 text-sm text-center py-4">Failed to load retention data.</p>
              )}
            </div>

            {/* GDPR Right-to-Erasure */}
            <div className="glass-panel p-6 rounded-3xl border border-rose-900/40 space-y-5">
              <div className="flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-rose-400" />
                <h2 className="font-heading font-bold text-white">GDPR Right-to-Erasure</h2>
                <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-950/40 border border-rose-800/50 text-rose-400">Admin Only</span>
              </div>

              <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/30 flex items-start gap-2">
                <Lock className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <p className="text-rose-300 text-xs leading-relaxed">
                  This operation permanently and irreversibly deletes all data associated with a candidate — including applications, scores, assessments, transcripts, and feedback — across all tables. This action <strong>cannot be undone</strong>. Only use in response to a verified GDPR erasure request.
                </p>
              </div>

              {eraseResult && (
                <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/30 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-emerald-300 font-semibold text-sm">Candidate data erased successfully</p>
                    <p className="text-emerald-400/70 text-xs mt-0.5">Tables cleared: {eraseResult.tables_cleared?.join(', ')}</p>
                    <p className="text-emerald-400/50 text-xs">Timestamp: {fmtTime(eraseResult.timestamp)}</p>
                  </div>
                </div>
              )}
              {eraseError && (
                <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/40 text-rose-300 text-sm flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />{eraseError}
                </div>
              )}

              <div className="space-y-3">
                <div>
                  <label className="block text-slate-400 text-xs font-semibold mb-1.5">Candidate UUID *</label>
                  <input
                    type="text"
                    value={eraseId}
                    onChange={e => { setEraseId(e.target.value); setConfirmErase(false); }}
                    placeholder="e.g. 3f8e4b1c-2a7d-4c90-b123-..."
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-rose-600 font-mono"
                  />
                </div>

                {eraseId.trim() && !confirmErase && (
                  <button
                    onClick={() => setConfirmErase(true)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 hover:bg-rose-900/50 font-bold text-sm transition-all"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    I understand — show confirmation
                    <ChevronRight className="w-4 h-4" />
                  </button>
                )}

                {confirmErase && (
                  <div className="p-4 rounded-xl border border-rose-700 bg-rose-950/30 space-y-3">
                    <p className="text-rose-200 font-bold text-sm">⚠️ Final Confirmation Required</p>
                    <p className="text-rose-300 text-xs">You are about to permanently erase all data for candidate ID: <code className="font-mono bg-slate-900 px-1.5 py-0.5 rounded text-rose-200">{eraseId}</code>. This cannot be reversed.</p>
                    <div className="flex gap-2">
                      <button
                        onClick={handleErase}
                        disabled={erasing}
                        className="flex items-center gap-2 px-5 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl font-bold text-sm"
                      >
                        {erasing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                        Permanently Erase All Data
                      </button>
                      <button onClick={() => setConfirmErase(false)} className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-sm">
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Teammates Directory & Invitations */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Create Member */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 md:col-span-1">
                <div className="flex items-center gap-2">
                  <UserPlus className="w-4 h-4 text-emerald-400" />
                  <h2 className="font-heading font-bold text-white">Create Teammate</h2>
                </div>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Add new team members with custom-tailored role-level visibility limits.
                </p>

                <form onSubmit={handleInvite} className="space-y-3">
                  {inviteSuccess && (
                    <div className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-800/30 text-emerald-300 text-xs">
                      {inviteSuccess}
                    </div>
                  )}
                  {inviteError && (
                    <div className="p-2.5 rounded-xl bg-rose-950/20 border border-rose-800/40 text-rose-300 text-xs">
                      {inviteError}
                    </div>
                  )}

                  <div>
                    <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={inviteForm.full_name}
                      onChange={e => setInviteForm(prev => ({ ...prev, full_name: e.target.value }))}
                      placeholder="e.g. Jane Recruiter"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      value={inviteForm.email}
                      onChange={e => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="e.g. jane@company.com"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Password</label>
                    <input
                      type="password"
                      required
                      value={inviteForm.password}
                      onChange={e => setInviteForm(prev => ({ ...prev, password: e.target.value }))}
                      placeholder="••••••••"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">System Role</label>
                    <select
                      value={inviteForm.role}
                      onChange={e => setInviteForm(prev => ({ ...prev, role: e.target.value }))}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
                    >
                      <option value="admin">Admin</option>
                      <option value="recruiter">Recruiter</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={inviting}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
                  >
                    {inviting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Add to Team</span>
                  </button>
                </form>
              </div>

              {/* Teammates Directory */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 md:col-span-2 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-blue-400" />
                      <h2 className="font-heading font-bold text-white">Active Team Directory</h2>
                    </div>
                    <button onClick={loadTeammates} className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white">
                      <RefreshCw className="w-3 h-3" />
                    </button>
                  </div>

                  {loadingTeammates ? (
                    <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
                  ) : teammates.length > 0 ? (
                    <div className="overflow-hidden rounded-2xl border border-slate-800">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-900/60">
                          <tr>
                            {['Teammate Name', 'Email Address', 'Configured Role'].map(h => (
                              <th key={h} className="px-4 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {teammates.map((u, i) => (
                            <tr key={i} className="hover:bg-slate-900/40 transition-colors">
                              <td className="px-4 py-2.5 font-semibold text-white">{u.full_name}</td>
                              <td className="px-4 py-2.5 text-slate-400 font-mono">{u.email}</td>
                              <td className="px-4 py-2.5">
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                  u.role === 'ADMIN' ? 'bg-rose-950/40 border-rose-800/40 text-rose-300' :
                                  u.role === 'RECRUITER' ? 'bg-blue-950/40 border-blue-800/40 text-blue-300' :
                                  u.role === 'HIRING_MANAGER' ? 'bg-purple-950/40 border-purple-800/40 text-purple-300' :
                                  u.role === 'INTERVIEWER' ? 'bg-amber-950/40 border-amber-800/40 text-amber-300' :
                                  'bg-slate-950/40 border-slate-800/40 text-slate-400'
                                }`}>{u.role}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-center text-slate-600 text-xs py-12">No active teammates found.</p>
                  )}
                </div>

                <div className="p-3.5 rounded-2xl bg-blue-950/20 border border-blue-800/30 flex items-start gap-2 text-[10px] text-blue-300 leading-relaxed mt-4">
                  <Key className="w-3.5 h-3.5 shrink-0 mt-0.5 text-blue-400" />
                  <div>
                    <strong>Role Levels & Limitations:</strong>
                    <ul className="list-disc pl-4 mt-1 space-y-1">
                      <li><strong>Admin</strong>: Complete capability over GDPR deletion, reports, integrations and templates.</li>
                      <li><strong>Recruiter</strong>: Manage jobs and review matches. Blocked from administrative overrides and compliance features.</li>
                      <li><strong>Hiring Manager & Interviewer</strong>: Scope-assigned review and feedback submission only.</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Audit Log */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <h2 className="font-heading font-bold text-white">Pipeline Audit Trail</h2>
                  <span className="text-[10px] text-slate-500 font-medium">Last 50 events</span>
                </div>
                <button onClick={loadAudit} className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 hover:text-white">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>

              {loadingAudit ? (
                <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
              ) : auditLog.length > 0 ? (
                <div className="overflow-hidden rounded-2xl border border-slate-800">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-900/60">
                      <tr>
                        {['Candidate ID', 'Action / Stage', 'Timestamp'].map(h => (
                          <th key={h} className="px-4 py-3 text-left text-[10px] font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {auditLog.map((entry, i) => (
                        <tr key={i} className="hover:bg-slate-900/40 transition-colors">
                          <td className="px-4 py-2.5 font-mono text-slate-400 text-[10px]">{entry.candidate_id?.slice(0, 12)}…</td>
                          <td className="px-4 py-2.5">
                            <span className="px-2 py-0.5 rounded-full bg-blue-950/40 border border-blue-800/40 text-blue-300 font-semibold capitalize">{entry.action?.replace(/_/g, ' ')}</span>
                          </td>
                          <td className="px-4 py-2.5 text-slate-500">{fmtTime(entry.timestamp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-center text-slate-650 text-sm py-8">No audit events found.</p>
              )}
            </div>
          </>
        ) : activeSettingsTab === 'campaigns' ? (
          /* Campaigns Settings Tab */
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Create Campaign Template */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 md:col-span-1">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-purple-400" />
                <h2 className="font-heading font-bold text-white">Create Drip Trigger</h2>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                Add automated Email or WhatsApp template prompts that send to candidates when they transition stage.
              </p>

              <form onSubmit={handleCreateCampaign} className="space-y-3">
                {campaignSuccess && (
                  <div className="p-2.5 rounded-xl bg-emerald-950/20 border border-emerald-800/30 text-emerald-300 text-xs">
                    {campaignSuccess}
                  </div>
                )}
                {campaignError && (
                  <div className="p-2.5 rounded-xl bg-rose-950/20 border border-rose-800/40 text-rose-300 text-xs">
                    {campaignError}
                  </div>
                )}

                <div>
                  <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Trigger Stage</label>
                  <select
                    value={campaignForm.trigger_stage}
                    onChange={e => setCampaignForm(prev => ({ ...prev, trigger_stage: e.target.value }))}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="screening">Screening</option>
                    <option value="interviewing">Interviewing</option>
                    <option value="offered">Offered</option>
                    <option value="hired">Hired</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Outreach Channel</label>
                  <select
                    value={campaignForm.channel}
                    onChange={e => setCampaignForm(prev => ({ ...prev, channel: e.target.value }))}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="email">Email</option>
                    <option value="whatsapp">WhatsApp</option>
                  </select>
                </div>

                {campaignForm.channel === 'email' && (
                  <div>
                    <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Subject Title</label>
                    <input
                      type="text"
                      required
                      value={campaignForm.subject}
                      onChange={e => setCampaignForm(prev => ({ ...prev, subject: e.target.value }))}
                      placeholder="Subject Line"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-slate-400 text-[10px] font-bold uppercase tracking-wider mb-1">Content Body</label>
                  <textarea
                    rows={4}
                    required
                    value={campaignForm.body}
                    onChange={e => setCampaignForm(prev => ({ ...prev, body: e.target.value }))}
                    placeholder="Outreach content. Supports {candidate_name} dynamic variables."
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none resize-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-lg"
                >
                  <span>Add Trigger template</span>
                </button>
              </form>
            </div>

            {/* Campaign Templates List */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4 md:col-span-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-purple-400" />
                  <h2 className="font-heading font-bold text-white">Active Outreach Sequences</h2>
                </div>
              </div>

              {loadingCampaigns ? (
                <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
              ) : campaigns.length > 0 ? (
                <div className="space-y-3">
                  {campaigns.map((tmpl) => (
                    <div key={tmpl.id} className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex justify-between gap-4">
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-blue-950/40 border border-blue-800/40 text-blue-300 text-[10px] font-bold uppercase">{tmpl.channel}</span>
                          <span className="px-2 py-0.5 rounded bg-purple-950/40 border border-purple-800/40 text-purple-300 text-[10px] font-bold uppercase">{tmpl.trigger_stage}</span>
                        </div>
                        {tmpl.subject && <h4 className="text-white font-bold text-sm truncate mt-1">{tmpl.subject}</h4>}
                        <p className="text-slate-400 text-xs leading-relaxed mt-0.5 whitespace-pre-wrap">{tmpl.body}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteCampaign(tmpl.id)}
                        className="p-1.5 rounded-lg bg-rose-950/20 border border-rose-900/30 text-rose-450 hover:bg-rose-900/40 self-start shrink-0 text-xs font-semibold"
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-650 text-xs py-12">No active outreach sequences defined yet.</p>
              )}
            </div>
          </div>
        ) : (
          /* NPS Dashboard Tab */
          <div className="space-y-6">
            {loadingNps ? (
              <div className="flex justify-center py-12"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>
            ) : npsData ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Metrics Breakdown Column */}
                <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-6 md:col-span-1">
                  <div className="text-center py-4">
                    <p className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Overall Experience NPS</p>
                    <h2 className="text-6xl font-extrabold font-heading text-white mt-2">{npsData.nps_score}</h2>
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold mt-3 ${
                      npsData.nps_score >= 50 ? 'bg-emerald-950/40 border border-emerald-800/40 text-emerald-300' :
                      npsData.nps_score >= 10 ? 'bg-amber-950/40 border border-amber-800/40 text-amber-300' :
                      'bg-rose-950/40 border border-rose-800/40 text-rose-300'
                    }`}>
                      {npsData.nps_score >= 50 ? 'Excellent candidate experience' :
                       npsData.nps_score >= 10 ? 'Healthy score' :
                       'Needs optimization review'}
                    </span>
                  </div>

                  <div className="border-t border-slate-800 pt-5 space-y-4">
                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-emerald-400">Promoters (9-10)</span>
                        <span className="text-white">{npsData.promoters} ({npsData.total_responses ? Math.round((npsData.promoters / npsData.total_responses) * 100) : 0}%)</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5">
                        <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${npsData.total_responses ? (npsData.promoters / npsData.total_responses) * 100 : 0}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-amber-400">Passives (7-8)</span>
                        <span className="text-white">{npsData.passives} ({npsData.total_responses ? Math.round((npsData.passives / npsData.total_responses) * 100) : 0}%)</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5">
                        <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${npsData.total_responses ? (npsData.passives / npsData.total_responses) * 100 : 0}%` }}></div>
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold mb-1">
                        <span className="text-rose-400">Detractors (0-6)</span>
                        <span className="text-white">{npsData.detractors} ({npsData.total_responses ? Math.round((npsData.detractors / npsData.total_responses) * 100) : 0}%)</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5">
                        <div className="bg-rose-500 h-1.5 rounded-full" style={{ width: `${npsData.total_responses ? (npsData.detractors / npsData.total_responses) * 100 : 0}%` }}></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Candidate Feed Column */}
                <div className="glass-panel p-6 rounded-3xl border border-slate-800 md:col-span-2 space-y-4 flex flex-col">
                  <div>
                    <h3 className="font-heading font-extrabold text-white text-lg">Candidate Experience Feedback</h3>
                    <p className="text-slate-400 text-xs mt-0.5">Aggregate candidate survey responses</p>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[420px]">
                    {npsData.reviews?.length > 0 ? (
                      npsData.reviews.map((rev) => (
                        <div key={rev.id} className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 flex gap-4 items-start">
                          <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center font-bold text-sm ${
                            rev.score >= 9 ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50' :
                            rev.score >= 7 ? 'bg-amber-950/80 text-amber-400 border border-amber-800/50' :
                            'bg-rose-950/80 text-rose-400 border border-rose-800/50'
                          }`}>
                            {rev.score}
                          </div>
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-white">{rev.candidate_name}</span>
                              <span className="text-[10px] text-slate-500">{new Date(rev.submitted_at).toLocaleDateString()}</span>
                            </div>
                            {rev.comment ? (
                              <p className="text-slate-350 text-xs italic">"{rev.comment}"</p>
                            ) : (
                              <p className="text-slate-500 text-xs italic">No additional review comment provided.</p>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-center text-slate-600 text-xs py-12">No candidate survey feedback reviews received yet.</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-center text-slate-500 text-sm">Failed to retrieve Net Promoter Score statistics.</p>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
