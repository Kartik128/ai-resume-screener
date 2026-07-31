import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { Sparkles, Check, Edit2, Plus, Trash2, Send, MessageSquare, Briefcase, MapPin, DollarSign, Clock, Users, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function JdPreparation() {
  const navigate = useNavigate();
  
  // Creation Form Inputs
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Engineering');
  const [location, setLocation] = useState('San Francisco, CA');
  const [isRemote, setIsRemote] = useState(false);
  const [skillInput, setSkillInput] = useState('');
  const [skills, setSkills] = useState([]);
  
  // App States
  const [generating, setGenerating] = useState(false);
  const [currentJob, setCurrentJob] = useState(null); // The loaded draft Job
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [approving, setApproving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Editing Fields
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editMinSalary, setEditMinSalary] = useState('');
  const [editMaxSalary, setEditMaxSalary] = useState('');
  const [editMinExp, setEditMinExp] = useState('');
  const [editMaxExp, setEditMaxExp] = useState('');
  const [editLocation, setEditLocation] = useState('');
  const [editRemote, setEditRemote] = useState(false);
  const [responsibilities, setResponsibilities] = useState([]);
  const [newResp, setNewResp] = useState('');

  const handleAddSkill = (e) => {
    e.preventDefault();
    if (skillInput.trim() && !skills.includes(skillInput.trim())) {
      setSkills([...skills, skillInput.trim()]);
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (idx) => {
    setSkills(skills.filter((_, i) => i !== idx));
  };

  // Generate JD via backend
  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!title) return;
    setGenerating(true);
    setErrorMsg('');
    try {
      const res = await api.post('/jobs/generate-ai', {
        title,
        department,
        key_skills: skills,
        location,
        is_remote: isRemote
      });
      loadJobToEditor(res.data);
      setSuccessMsg('AI Job Description generated successfully! You can now review, edit, and collaborate.');
    } catch {
      setErrorMsg('Failed to generate Job Description.');
    }
    setGenerating(false);
  };

  const loadJobToEditor = (job) => {
    setCurrentJob(job);
    setEditTitle(job.title);
    setEditDesc(job.raw_description);
    setEditMinSalary(job.min_salary || '');
    setEditMaxSalary(job.max_salary || '');
    setEditMinExp(job.min_experience_years || '');
    setEditMaxExp(job.max_experience_years || '');
    setEditLocation(job.location || '');
    setEditRemote(job.is_remote);
    setResponsibilities(job.responsibilities || []);
    fetchComments(job.id);
  };

  const fetchComments = async (jobId) => {
    try {
      const res = await api.get(`/jobs/${jobId}/comments`);
      setComments(res.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || !currentJob) return;
    setSubmittingComment(true);
    try {
      const res = await api.post(`/jobs/${currentJob.id}/comments`, {
        comment_text: newComment
      });
      setComments([...comments, res.data]);
      setNewComment('');
    } catch {
      setErrorMsg('Failed to publish comment.');
    }
    setSubmittingComment(false);
  };

  const handleAddResponsibility = () => {
    if (newResp.trim() && !responsibilities.includes(newResp.trim())) {
      setResponsibilities([...responsibilities, newResp.trim()]);
      setNewResp('');
    }
  };

  const handleRemoveResponsibility = (idx) => {
    setResponsibilities(responsibilities.filter((_, i) => i !== idx));
  };

  // Save edits on draft
  const handleSaveEdits = async () => {
    if (!currentJob) return;
    setSaving(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await api.put(`/jobs/${currentJob.id}`, {
        title: editTitle,
        department: currentJob.department,
        raw_description: editDesc,
        status: currentJob.status,
        min_experience_years: editMinExp ? Number(editMinExp) : null,
        max_experience_years: editMaxExp ? Number(editMaxExp) : null,
        education_requirement: currentJob.education_requirement,
        location: editLocation,
        is_remote: editRemote,
        min_salary: editMinSalary ? Number(editMinSalary) : null,
        max_salary: editMaxSalary ? Number(editMaxSalary) : null,
        salary_currency: currentJob.salary_currency || 'USD',
        responsibilities: responsibilities,
        mandatory_skills: currentJob.job_skills?.filter(s => s.is_mandatory).map(s => ({ name: s.skill?.name, category: s.skill?.category })) || [],
        good_to_have_skills: currentJob.job_skills?.filter(s => !s.is_mandatory).map(s => ({ name: s.skill?.name, category: s.skill?.category })) || []
      });
      loadJobToEditor(res.data);
      setSuccessMsg('Draft modifications saved successfully.');
    } catch {
      setErrorMsg('Failed to save draft edits.');
    }
    setSaving(false);
  };

  // Approve & finalize draft
  const handleApprove = async () => {
    if (!currentJob) return;
    setApproving(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      await api.post(`/jobs/${currentJob.id}/approve`);
      setSuccessMsg('JD Approved and Published! Redirecting back to Job Openings...');
      setTimeout(() => {
        navigate('/jobs');
      }, 1500);
    } catch {
      setErrorMsg('Failed to approve and finalize JD.');
    }
    setApproving(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Navigation header */}
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate('/jobs')} 
            className="flex items-center space-x-2 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Job Openings</span>
          </button>
          
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-yellow-450 animate-pulse"></span>
            <span className="text-xs font-semibold text-yellow-450 uppercase tracking-wide">AI Generation Workspace</span>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs">
            {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 text-xs">
            {successMsg}
          </div>
        )}

        {!currentJob ? (
          /* Step 1: Input Builder Form */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-panel p-8 rounded-3xl border border-slate-800 space-y-6">
              <div>
                <Sparkles className="w-8 h-8 text-blue-400 mb-2" />
                <h1 className="font-heading font-extrabold text-2xl text-white">AI Job Description Builder</h1>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Provide minimal inputs below, and our advanced AI model will automatically draft target skills, detailed responsibilities, optimal salary structures, and location tags.
                </p>
              </div>

              <form onSubmit={handleGenerate} className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Target Job Role / Title *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Senior Backend Engineer"
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Department</label>
                    <select
                      value={department}
                      onChange={e => setDepartment(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                    >
                      {['Engineering', 'Product', 'Design', 'Marketing', 'Sales', 'Finance', 'HR'].map(d => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-slate-400 mb-1 font-semibold">Location</label>
                    <input
                      type="text"
                      placeholder="e.g. San Francisco, CA"
                      value={location}
                      onChange={e => setLocation(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none"
                    />
                  </div>
                  <div className="flex items-center h-full pt-6">
                    <label className="flex items-center space-x-2 text-slate-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={isRemote}
                        onChange={e => setIsRemote(e.target.checked)}
                        className="rounded border-slate-800 bg-slate-900 text-blue-600 focus:ring-0 focus:ring-offset-0"
                      />
                      <span>Is this a remote role?</span>
                    </label>
                  </div>
                </div>

                {/* Key Skills Tags Input */}
                <div className="space-y-2">
                  <label className="block text-slate-400 font-semibold">Focus Skills (Optional)</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="e.g. Python"
                      value={skillInput}
                      onChange={e => setSkillInput(e.target.value)}
                      className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleAddSkill}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg border border-slate-700 font-semibold"
                    >
                      Add
                    </button>
                  </div>
                  
                  {skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {skills.map((s, idx) => (
                        <span key={idx} className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                          <span>{s}</span>
                          <button type="button" onClick={() => handleRemoveSkill(idx)} className="text-blue-500 hover:text-blue-300 font-bold">×</button>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={generating || !title}
                  className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 disabled:opacity-50 text-white font-extrabold rounded-xl flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20"
                >
                  {generating ? (
                    <span>Drafting JD via Gemini AI...</span>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Generate Draft JD</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="glass-panel p-6 rounded-3xl border border-slate-800 flex flex-col justify-center space-y-4 text-center">
              <Briefcase className="w-12 h-12 text-slate-600 mx-auto" />
              <div>
                <h3 className="font-bold text-white text-base">Standardized Drafts</h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Generated drafts are saved in <span className="text-yellow-400 font-semibold">DRAFT</span> status, making it safe to collaborate and iterate with teammates before making them public for applicants.
                </p>
              </div>
            </div>
          </div>
        ) : (
          /* Step 2: Interactive Review, Edit & Collaboration Panel */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Editor Workspace Column */}
            <div className="lg:col-span-2 glass-panel p-6 rounded-3xl border border-slate-800 space-y-6">
              
              {/* Draft Info Header */}
              <div className="flex justify-between items-center border-b border-slate-850 pb-4">
                <div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-yellow-950 text-yellow-400 border border-yellow-800">
                    Draft Workspace
                  </span>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={e => setEditTitle(e.target.value)}
                    className="font-heading font-extrabold text-xl text-white bg-transparent border-b border-transparent focus:border-slate-700 focus:outline-none block mt-1 w-full"
                  />
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={handleSaveEdits}
                    disabled={saving}
                    className="px-4 py-2 border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold"
                  >
                    {saving ? 'Saving...' : 'Save Edits'}
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={approving}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center space-x-1.5"
                  >
                    <Check className="w-4 h-4" />
                    <span>{approving ? 'Publishing...' : 'Approve & Finalize'}</span>
                  </button>
                </div>
              </div>

              {/* Input Fields details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Target Location</label>
                  <div className="relative">
                    <MapPin className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                    <input
                      type="text"
                      value={editLocation}
                      onChange={e => setEditLocation(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 pl-8 pr-3 py-2 rounded-lg text-white"
                    />
                  </div>
                </div>

                <div className="flex items-center pt-5">
                  <label className="flex items-center space-x-2 text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editRemote}
                      onChange={e => setEditRemote(e.target.checked)}
                      className="rounded border-slate-800 bg-slate-900 text-blue-600"
                    />
                    <span>Role is Remote</span>
                  </label>
                </div>
              </div>

              {/* Structured Metadata - Salaries & Experience */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Min Salary ($)</label>
                  <input
                    type="number"
                    value={editMinSalary}
                    onChange={e => setEditMinSalary(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Max Salary ($)</label>
                  <input
                    type="number"
                    value={editMaxSalary}
                    onChange={e => setEditMaxSalary(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Min Exp (Yrs)</label>
                  <input
                    type="number"
                    value={editMinExp}
                    onChange={e => setEditMinExp(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Max Exp (Yrs)</label>
                  <input
                    type="number"
                    value={editMaxExp}
                    onChange={e => setEditMaxExp(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg text-white"
                  />
                </div>
              </div>

              {/* Raw Text description box */}
              <div className="space-y-1.5 text-xs">
                <label className="block text-slate-400 font-semibold">Summary / Description</label>
                <textarea
                  rows={5}
                  value={editDesc}
                  onChange={e => setEditDesc(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-white focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              {/* Responsibilities interactive editor */}
              <div className="space-y-3 text-xs">
                <label className="block text-slate-400 font-semibold">Key Responsibilities</label>
                
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="e.g. Design core software modules"
                    value={newResp}
                    onChange={e => setNewResp(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-white placeholder-slate-650"
                  />
                  <button
                    type="button"
                    onClick={handleAddResponsibility}
                    className="px-3 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-2">
                  {responsibilities.map((r, idx) => (
                    <div key={idx} className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800">
                      <span className="text-slate-300 leading-normal">{r}</span>
                      <button 
                        onClick={() => handleRemoveResponsibility(idx)}
                        className="p-1 rounded hover:bg-rose-950/40 text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Collaborative Comments Side Drawer */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800 flex flex-col h-full space-y-4">
              <div className="flex items-center space-x-2 border-b border-slate-850 pb-3">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                <h3 className="font-heading font-bold text-white text-sm">Review Comments</h3>
              </div>

              {/* Comment Thread Timeline */}
              <div className="flex-1 overflow-y-auto max-h-[300px] space-y-3 pr-1 text-xs">
                {comments.length > 0 ? (
                  comments.map(c => {
                    const initials = c.user_name ? c.user_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'U';
                    return (
                      <div key={c.id} className="p-3 rounded-2xl bg-slate-900 border border-slate-800/80 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div className="h-6 w-6 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-[10px]">
                              {initials}
                            </div>
                            <span className="font-bold text-white text-[11px]">{c.user_name}</span>
                          </div>
                          <span className="text-[9px] text-slate-500">{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <p className="text-slate-350 leading-relaxed text-[11px]">{c.comment_text}</p>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center text-slate-500 py-8 text-[11px]">
                    No feedback comments logged. Add a comment below to collaborate with your team.
                  </div>
                )}
              </div>

              {/* Leave a review comment */}
              <form onSubmit={handleAddComment} className="pt-2 border-t border-slate-850">
                <div className="flex gap-2">
                  <input
                    type="text"
                    required
                    placeholder="Ask peer to review/approve..."
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={submittingComment}
                    className="p-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </form>

            </div>

          </div>
        )}
      </main>
    </div>
  );
}
