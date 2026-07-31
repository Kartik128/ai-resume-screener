import React, { useState, useEffect } from 'react';
import { X, Mail, Calendar, Loader2, AlertCircle, Link, Trash2 } from 'lucide-react';
import api from '../services/api';

export default function IntegrationsModal({ applicationId, candidateId, jobId, candidateName, onClose }) {
  const [activeTab, setActiveTab] = useState('email');
  const [outreachTone, setOutreachTone] = useState('formal');
  const [generatingOutreach, setGeneratingOutreach] = useState(false);

  // Drag and Drop Popup panel position state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Webhook Hub States
  const [webhooks, setWebhooks] = useState([]);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookEvent, setWebhookEvent] = useState('candidate.stage_changed');
  const [savingWebhook, setSavingWebhook] = useState(false);
  const [loadingWebhooks, setLoadingWebhooks] = useState(false);

  // Email Form
  const [subject, setSubject] = useState(`TalentAI Interview Invitation — ${candidateName}`);
  const [emailBody, setEmailBody] = useState(`Hi ${candidateName},\n\nWe reviewed your application and would love to move you to the next round. Let us know your availability...`);
  const [emailSubmitting, setEmailSubmitting] = useState(false);

  // Calendar Form
  const [date, setDate] = useState('');
  const [duration, setDuration] = useState(30);
  const [interviewer, setInterviewer] = useState('hiring-manager@company.com');
  const [calendarSubmitting, setCalendarSubmitting] = useState(false);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [microsoftConnected, setMicrosoftConnected] = useState(false);
  const [activeProvider, setActiveProvider] = useState('smtp');
  const [checkingProviders, setCheckingProviders] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadProviderStatus = async () => {
    setCheckingProviders(true);
    try {
      const gRes = await api.get('/auth/google/status');
      setGoogleConnected(gRes.data.connected);
      const mRes = await api.get('/auth/microsoft/status');
      setMicrosoftConnected(mRes.data.connected);
      setActiveProvider(mRes.data.active_provider || 'smtp');
    } catch (e) {
      console.error(e);
    }
    setCheckingProviders(false);
  };

  // Load webhooks/provider statuses
  useEffect(() => {
    if (activeTab === 'webhooks') {
      setLoadingWebhooks(true);
      api.get('/webhooks/').then(res => {
        setWebhooks(res.data);
      }).catch(() => {}).finally(() => setLoadingWebhooks(false));
    } else if (activeTab === 'calendar') {
      loadProviderStatus();
    }
  }, [activeTab]);

  const handleConnectGoogle = async () => {
    try {
      const me = await api.get('/auth/me');
      const res = await api.get(`/auth/google?user_id=${me.data.id}`);
      window.open(res.data.url, '_blank');
    } catch {
      setError('Could not initialize Google OAuth loop.');
    }
  };

  const handleConnectMicrosoft = async () => {
    try {
      const res = await api.get('/auth/microsoft/connect');
      window.open(res.data.url, '_blank');
    } catch {
      setError('Could not initialize Microsoft OAuth loop.');
    }
  };

  const handleSelectProvider = async (provider) => {
    try {
      await api.post('/auth/provider', { provider });
      setActiveProvider(provider);
      setSuccess(`Active provider switched to ${provider.toUpperCase()}`);
    } catch {
      setError('Failed to switch active provider.');
    }
  };

  const handleMouseDown = (e) => {
    // Only drag from header bar handles
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

  const handleRegisterWebhook = async (e) => {
    e.preventDefault();
    if (!webhookUrl) return;
    setSavingWebhook(true);
    try {
      const res = await api.post('/webhooks/', { target_url: webhookUrl, event_type: webhookEvent });
      setWebhooks(prev => [...prev, res.data]);
      setWebhookUrl('');
      setSuccess('Webhook endpoint registered successfully!');
    } catch {
      setError('Failed to register webhook endpoint.');
    }
    setSavingWebhook(false);
  };

  const handleDeleteWebhook = async (id) => {
    try {
      await api.delete(`/webhooks/${id}`);
      setWebhooks(prev => prev.filter(w => w.id !== id));
    } catch {
      setError('Failed to remove webhook.');
    }
  };

  const generateAIOutreach = async () => {
    setGeneratingOutreach(true);
    setError('');
    try {
      const res = await api.post('/copilot/outreach', {
        job_id: jobId,
        candidate_id: candidateId,
        tone: outreachTone
      });
      setSubject(res.data.subject);
      setEmailBody(res.data.body);
    } catch (e) {
      setError('Failed to auto-generate outreach template.');
    }
    setGeneratingOutreach(false);
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    setEmailSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await api.post(`/pipeline/${applicationId}/send-email`, {
        subject: subject,
        body: emailBody
      });
      setSuccess('Email dispatched to candidate and logged to timeline!');
      setSubject('');
      setEmailBody('');
    } catch (e) {
      setError('Failed to dispatch email.');
    }
    setEmailSubmitting(false);
  };

  const handleSchedule = async (e) => {
    e.preventDefault();
    if (!date) {
      setError('Please select date and time.');
      return;
    }
    setCalendarSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await api.post(`/pipeline/${applicationId}/schedule-interview`, {
        scheduled_at: new Date(date).toISOString(),
        duration_mins: Number(duration),
        interviewer_email: interviewer
      });
      setSuccess('Google Calendar invite sent to candidate and logged to timeline!');
    } catch (e) {
      setError('Failed to schedule calendar event.');
    }
    setCalendarSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div 
        className="w-full max-w-lg rounded-2xl border border-blue-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(59,130,246,0.3)] flex flex-col pointer-events-auto" 
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          maxHeight: '80vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        
        {/* Drag-Header */}
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-blue-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-blue-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight font-heading flex items-center gap-1.5">
              <span className="text-blue-300">🎙️ Candidate Integrations</span>
              <span className="text-[9px] font-bold bg-blue-950 text-blue-300 border border-blue-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
            </h2>
            <p className="text-xs text-slate-350">Interact with: {candidateName}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 shrink-0 bg-slate-900/10 px-6 py-2.5 gap-2">
          <button
            onClick={() => setActiveTab('email')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'email' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Mail className="w-4 h-4" />
            <span>Send Email</span>
          </button>
          <button
            onClick={() => setActiveTab('calendar')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'calendar' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Schedule Calendar Interview</span>
          </button>
          <button
            onClick={() => setActiveTab('webhooks')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeTab === 'webhooks' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>🔗 Webhook Triggers</span>
          </button>
        </div>

        {/* Content panel */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl flex items-center gap-1.5"><AlertCircle className="w-4 h-4 text-rose-450" />{error}</div>}
          {success && <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 rounded-xl font-medium">{success}</div>}

          {activeTab === 'webhooks' ? (
            <div className="space-y-4">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <p className="text-slate-400 leading-relaxed">
                  Register external endpoints that receive <span className="text-blue-400 font-semibold">real-time HTTP POST</span> callbacks whenever candidate pipeline events fire (e.g. stage change, offer release). Connect your ATS, HRMS, Slack, or custom services.
                </p>
              </div>

              {/* Register new webhook */}
              <form onSubmit={handleRegisterWebhook} className="space-y-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Callback URL *</label>
                  <div className="relative">
                    <Link className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="url"
                      required
                      value={webhookUrl}
                      onChange={e => setWebhookUrl(e.target.value)}
                      placeholder="https://your-service.com/webhooks/talent"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-semibold">Event Type</label>
                  <select
                    value={webhookEvent}
                    onChange={e => setWebhookEvent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="candidate.stage_changed">candidate.stage_changed</option>
                    <option value="candidate.hired">candidate.hired</option>
                    <option value="offer.released">offer.released</option>
                    <option value="assessment.completed">assessment.completed</option>
                  </select>
                </div>
                <button
                  type="submit"
                  disabled={savingWebhook || !webhookUrl}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
                >
                  {savingWebhook && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Register Webhook</span>
                </button>
              </form>

              {/* Registered list */}
              {loadingWebhooks ? (
                <div className="text-center text-slate-500 py-4"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
              ) : webhooks.length > 0 ? (
                <div className="space-y-2">
                  <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Active Endpoints ({webhooks.length})</h4>
                  {webhooks.map(w => (
                    <div key={w.id} className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                      <div className="min-w-0">
                        <p className="text-emerald-400 font-mono text-[10px] truncate">{w.target_url}</p>
                        <p className="text-slate-500 text-[9px] mt-0.5">{w.event_type}</p>
                      </div>
                      <button onClick={() => handleDeleteWebhook(w.id)} className="shrink-0 p-1.5 rounded bg-rose-950/30 hover:bg-rose-900/50 text-rose-400 border border-rose-900/40 transition-colors">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-600 text-[11px] py-4">No webhook endpoints registered yet.</p>
              )}
            </div>
          ) : activeTab === 'email' ? (
            <form onSubmit={handleSendEmail} className="space-y-4">
              {/* AI Outreach Writer Block */}
              <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-900/30 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-purple-300 flex items-center gap-1">✨ AI Outreach Writer</span>
                  <select
                    value={outreachTone}
                    onChange={(e) => setOutreachTone(e.target.value)}
                    className="bg-slate-900 border border-slate-800 text-[10px] text-white px-2 py-1 rounded"
                  >
                    <option value="formal">Formal</option>
                    <option value="startup">Startup</option>
                    <option value="casual">Casual</option>
                    <option value="executive">Executive</option>
                  </select>
                </div>
                <p className="text-[10px] text-slate-400">Generate a custom engaging email based on this candidate's resume achievements.</p>
                <button
                  type="button"
                  disabled={generatingOutreach}
                  onClick={generateAIOutreach}
                  className="w-full py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded font-bold text-[10px]"
                >
                  {generatingOutreach ? 'Writing outreach copy...' : 'Generate AI Outreach'}
                </button>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Subject *</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Email Content Body *</label>
                <textarea
                  rows={6}
                  required
                  value={emailBody}
                  onChange={(e) => setEmailBody(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={emailSubmitting}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
              >
                {emailSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Send Email Invitation</span>
              </button>
            </form>
          ) : (
            checkingProviders ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Providers Cards Side-by-Side */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Google Calendar Card */}
                  <div className={`p-4 rounded-xl border transition-all ${
                    activeProvider === 'google' 
                      ? 'bg-blue-950/20 border-blue-500/60 shadow-lg shadow-blue-500/10' 
                      : 'bg-slate-900 border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-white text-xs">Google Workspace</span>
                      {googleConnected ? (
                        <span className="text-[9px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/40 px-1.5 py-0.5 rounded">Connected</span>
                      ) : (
                        <span className="text-[9px] font-bold bg-slate-950 text-slate-400 border border-slate-800 px-1.5 py-0.5 rounded">Offline</span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 mb-3">Sync Gmail and Google Calendar events.</p>
                    {googleConnected ? (
                      <button
                        type="button"
                        onClick={() => handleSelectProvider('google')}
                        className={`w-full py-1.5 rounded-lg text-[10px] font-bold transition-all ${
                          activeProvider === 'google'
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        }`}
                      >
                        {activeProvider === 'google' ? 'Active Provider' : 'Set Active'}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={handleConnectGoogle}
                        className="w-full py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-800/40 rounded-lg text-[10px] font-bold transition-all"
                      >
                        Connect Google
                      </button>
                    )}
                  </div>

                  {/* Microsoft Outlook Card */}
                  <div className={`p-4 rounded-xl border transition-all ${
                    activeProvider === 'microsoft' 
                      ? 'bg-blue-950/20 border-blue-500/60 shadow-lg shadow-blue-500/10' 
                      : 'bg-slate-900 border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-white text-xs">Microsoft 365</span>
                      {microsoftConnected ? (
                        <span className="text-[9px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/40 px-1.5 py-0.5 rounded">Connected</span>
                      ) : (
                        <span className="text-[9px] font-bold bg-slate-950 text-slate-400 border border-slate-800 px-1.5 py-0.5 rounded">Offline</span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 mb-3">Sync Outlook Mail and Teams Calendars.</p>
                    {microsoftConnected ? (
                      <button
                        type="button"
                        onClick={() => handleSelectProvider('microsoft')}
                        className={`w-full py-1.5 rounded-lg text-[10px] font-bold transition-all ${
                          activeProvider === 'microsoft'
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                        }`}
                      >
                        {activeProvider === 'microsoft' ? 'Active Provider' : 'Set Active'}
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={handleConnectMicrosoft}
                        className="w-full py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-800/40 rounded-lg text-[10px] font-bold transition-all"
                      >
                        Connect Microsoft
                      </button>
                    )}
                  </div>
                </div>

                {/* Booking Form */}
                <form onSubmit={handleSchedule} className="space-y-4 pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800 text-[10px]">
                    <span className="text-slate-400 font-semibold">Active Dispatch Mode:</span>
                    <span className="font-bold text-blue-400 uppercase">{activeProvider}</span>
                  </div>

                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Select Date & Time *</label>
                    <input
                      type="datetime-local"
                      required
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-slate-400 mb-1 font-semibold">Duration (minutes)</label>
                      <select
                        value={duration}
                        onChange={(e) => setDuration(Number(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none"
                      >
                        {[15, 30, 45, 60, 90, 120].map(d => (
                          <option key={d} value={d}>{d} minutes</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-semibold">Interviewer Email *</label>
                      <input
                        type="email"
                        required
                        value={interviewer}
                        onChange={(e) => setInterviewer(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={calendarSubmitting}
                    className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-blue-500/25"
                  >
                    {calendarSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Create Calendar Meeting</span>
                  </button>
                </form>
              </div>
            )
          )}
        </div>

      </div>
    </div>
  );
}
