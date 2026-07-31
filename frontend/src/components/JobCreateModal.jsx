import React, { useState } from 'react';
import { Sparkles, Upload, FileText, Plus, X, CheckCircle2, MapPin, Briefcase, DollarSign, GraduationCap, ClipboardList } from 'lucide-react';
import api from '../services/api';

export default function JobCreateModal({ onClose, onCreated }) {
  const [activeTab, setActiveTab] = useState('paste');
  const [rawText, setRawText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [newMandatorySkill, setNewMandatorySkill] = useState('');
  const [newGoodSkill, setNewGoodSkill] = useState('');
  const [newResponsibility, setNewResponsibility] = useState('');

  const handleParse = async () => {
    setLoading(true);
    try {
      let res;
      if (activeTab === 'paste') {
        res = await api.post('/jobs/parse-text', { raw_description: rawText });
      } else {
        const formData = new FormData();
        formData.append('file', file);
        res = await api.post('/jobs/parse-file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      setExtractedData(res.data);
    } catch (e) {
      console.error(e);
      alert('Failed to parse JD. Please check your input and try again.');
    }
    setLoading(false);
  };

  const handleAddMandatorySkill = () => {
    if (!newMandatorySkill.trim()) return;
    setExtractedData((prev) => ({
      ...prev,
      mandatory_skills: [...(prev.mandatory_skills || []), { name: newMandatorySkill.trim(), category: 'Custom', synonyms: [] }]
    }));
    setNewMandatorySkill('');
  };

  const handleRemoveMandatorySkill = (index) => {
    setExtractedData((prev) => ({
      ...prev,
      mandatory_skills: prev.mandatory_skills.filter((_, i) => i !== index)
    }));
  };

  const handleAddGoodSkill = () => {
    if (!newGoodSkill.trim()) return;
    setExtractedData((prev) => ({
      ...prev,
      good_to_have_skills: [...(prev.good_to_have_skills || []), { name: newGoodSkill.trim(), category: 'Custom', synonyms: [] }]
    }));
    setNewGoodSkill('');
  };

  const handleRemoveGoodSkill = (index) => {
    setExtractedData((prev) => ({
      ...prev,
      good_to_have_skills: prev.good_to_have_skills.filter((_, i) => i !== index)
    }));
  };

  const handleAddResponsibility = () => {
    if (!newResponsibility.trim()) return;
    setExtractedData((prev) => ({
      ...prev,
      responsibilities: [...(prev.responsibilities || []), newResponsibility.trim()]
    }));
    setNewResponsibility('');
  };

  const handleRemoveResponsibility = (index) => {
    setExtractedData((prev) => ({
      ...prev,
      responsibilities: prev.responsibilities.filter((_, i) => i !== index)
    }));
  };

  const handleFieldChange = (field, value) => {
    setExtractedData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveJob = async () => {
    if (!extractedData?.role?.trim()) {
      alert('Please enter a Job Role Title before saving.');
      return;
    }
    if (!extractedData?.mandatory_skills?.length) {
      alert('Please add at least one mandatory skill before saving.');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        title: extractedData.role,
        department: extractedData.department || 'General',
        raw_description: rawText || 'Job description document uploaded.',
        status: 'active',
        min_experience_years: parseFloat(extractedData.min_experience_years) || 0,
        max_experience_years: parseFloat(extractedData.max_experience_years) || 10,
        education_requirement: extractedData.education_requirement || '',
        location: extractedData.location || '',
        is_remote: extractedData.is_remote || false,
        blind_mode: extractedData.blind_mode || false,
        min_salary: parseFloat(extractedData.min_salary) || null,
        max_salary: parseFloat(extractedData.max_salary) || null,
        salary_currency: extractedData.salary_currency || 'USD',
        responsibilities: extractedData.responsibilities || [],
        mandatory_skills: extractedData.mandatory_skills || [],
        good_to_have_skills: extractedData.good_to_have_skills || [],
      };
      await api.post('/jobs/', payload);
      onCreated();
      onClose();
    } catch (e) {
      console.error(e);
      alert('Failed to save job. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-3xl p-6 rounded-2xl max-h-[92vh] overflow-y-auto border border-slate-700 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <h3 className="font-heading font-bold text-xl text-white flex items-center">
            <Sparkles className="w-5 h-5 text-blue-400 mr-2" />
            {!extractedData ? 'Create Job Description' : 'Validate & Confirm Job Details'}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white font-bold text-lg leading-none">✕</button>
        </div>

        {!extractedData ? (
          /* ── Step 1: Input JD ── */
          <div className="mt-4 space-y-4">
            <div className="flex space-x-2 border-b border-slate-800 pb-2">
              <button
                onClick={() => setActiveTab('paste')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors ${
                  activeTab === 'paste' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Paste JD Text</span>
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-colors ${
                  activeTab === 'upload' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Upload className="w-4 h-4" />
                <span>Upload PDF / DOCX</span>
              </button>
            </div>

            {activeTab === 'paste' ? (
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste the full Job Description here. Include all sections: role title, responsibilities, required skills, preferred skills, experience, salary, and location."
                rows={10}
                className="w-full p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
              />
            ) : (
              <div className="p-8 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl text-center transition-colors">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="hidden"
                  id="jd-upload-input"
                />
                <label htmlFor="jd-upload-input" className="cursor-pointer block space-y-2">
                  <Upload className="w-8 h-8 text-blue-400 mx-auto" />
                  <p className="text-xs text-slate-300 font-medium">Click to select PDF, DOCX, or TXT file</p>
                  {file && <p className="text-xs text-emerald-400 font-bold mt-1">✓ {file.name}</p>}
                </label>
              </div>
            )}

            <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-900/40 text-xs text-blue-300">
              <strong>💡 Tip:</strong> The AI works best when you include the complete JD — job title, all required & preferred skills, years of experience, location, and responsibilities. The more detailed the JD, the better the candidate matching.
            </div>

            <button
              disabled={loading || (activeTab === 'paste' ? rawText.trim().length < 20 : !file)}
              onClick={handleParse}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold text-sm hover:opacity-95 disabled:opacity-40 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20 transition-opacity"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'AI Extracting Information...' : 'Extract & Analyze with AI'}</span>
            </button>
          </div>
        ) : (
          /* ── Step 2: Validate All Extracted Data ── */
          <div className="mt-4 space-y-5 text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>AI Extraction Complete — Review & Edit Before Saving</span>
              </div>
              <span className="text-[10px] text-slate-500">{(extractedData.mandatory_skills?.length || 0)} mandatory · {(extractedData.good_to_have_skills?.length || 0)} preferred skills found</span>
            </div>

            {/* Row 1: Role Title & Department */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                  <Briefcase className="w-3.5 h-3.5" /> <span>Job Role Title *</span>
                </label>
                <input
                  type="text"
                  value={extractedData.role || ''}
                  onChange={(e) => handleFieldChange('role', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                  placeholder="e.g. Senior Software Engineer"
                />
              </div>
              <div>
                <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                  <Briefcase className="w-3.5 h-3.5" /> <span>Department</span>
                </label>
                <input
                  type="text"
                  value={extractedData.department || ''}
                  onChange={(e) => handleFieldChange('department', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                  placeholder="e.g. Engineering, Finance, HR"
                />
              </div>
            </div>

            {/* Row 2: Experience, Location, Remote */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-slate-400 mb-1.5 font-semibold">Min Exp (Yrs)</label>
                <input
                  type="number"
                  min="0"
                  value={extractedData.min_experience_years ?? ''}
                  onChange={(e) => handleFieldChange('min_experience_years', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1.5 font-semibold">Max Exp (Yrs)</label>
                <input
                  type="number"
                  min="0"
                  value={extractedData.max_experience_years ?? ''}
                  onChange={(e) => handleFieldChange('max_experience_years', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                />
              </div>
              <div>
                <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                  <MapPin className="w-3.5 h-3.5" /> <span>Location</span>
                </label>
                <input
                  type="text"
                  value={extractedData.location || ''}
                  onChange={(e) => handleFieldChange('location', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                  placeholder="City, State or Remote"
                />
              </div>
            </div>

            {/* Row 3: Salary & Remote Flag */}
            <div className="grid grid-cols-4 gap-3">
              <div>
                <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                  <DollarSign className="w-3.5 h-3.5" /> <span>Min Salary</span>
                </label>
                <input
                  type="number"
                  value={extractedData.min_salary ?? ''}
                  onChange={(e) => handleFieldChange('min_salary', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                  placeholder="e.g. 80000"
                />
              </div>
              <div>
                <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                  <DollarSign className="w-3.5 h-3.5" /> <span>Max Salary</span>
                </label>
                <input
                  type="number"
                  value={extractedData.max_salary ?? ''}
                  onChange={(e) => handleFieldChange('max_salary', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                  placeholder="e.g. 130000"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1.5 font-semibold">Currency</label>
                <select
                  value={extractedData.salary_currency || 'USD'}
                  onChange={(e) => handleFieldChange('salary_currency', e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                >
                  {['USD', 'GBP', 'EUR', 'INR', 'AUD', 'CAD', 'SGD', 'AED'].map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1.5 font-semibold">Remote?</label>
                <select
                  value={extractedData.is_remote ? 'true' : 'false'}
                  onChange={(e) => handleFieldChange('is_remote', e.target.value === 'true')}
                  className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                >
                  <option value="false">On-Site / Hybrid</option>
                  <option value="true">Fully Remote</option>
                </select>
              </div>
            </div>

            {/* Row 4: Blind Mode toggle */}
            <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-900/40 text-xs flex items-center justify-between">
              <div>
                <span className="font-semibold text-purple-300 block mb-0.5">🔒 Enable Bias-Reduction Blind Scoring Mode</span>
                <p className="text-[10px] text-slate-400">Hides name, email, phone, location, and educational institutions during initial scoring to prevent unconscious bias.</p>
              </div>
              <select
                value={extractedData.blind_mode ? 'true' : 'false'}
                onChange={(e) => handleFieldChange('blind_mode', e.target.value === 'true')}
                className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-white px-3 py-1.5 font-semibold focus:outline-none focus:border-purple-500"
              >
                <option value="false">Disable</option>
                <option value="true">Enable</option>
              </select>
            </div>

            {/* Education */}
            <div>
              <label className="flex items-center space-x-1.5 text-slate-400 mb-1.5 font-semibold">
                <GraduationCap className="w-3.5 h-3.5" /> <span>Education Requirement</span>
              </label>
              <input
                type="text"
                value={extractedData.education_requirement || ''}
                onChange={(e) => handleFieldChange('education_requirement', e.target.value)}
                className="w-full p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-white focus:outline-none focus:border-blue-500 text-xs"
                placeholder="e.g. Bachelor's in Computer Science or equivalent experience"
              />
            </div>

            {/* Mandatory Skills */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-blue-900/50">
              <label className="block text-blue-300 font-bold mb-2">
                🔵 Mandatory Skills (Must-Have) — {extractedData.mandatory_skills?.length || 0} extracted
              </label>
              <div className="flex flex-wrap gap-1.5 mb-2.5 max-h-32 overflow-y-auto">
                {(extractedData.mandatory_skills || []).map((s, i) => (
                  <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-lg bg-blue-950/80 text-blue-300 border border-blue-700/60 font-semibold text-[11px]">
                    {s.name}
                    <button onClick={() => handleRemoveMandatorySkill(i)} className="ml-1.5 text-blue-400/60 hover:text-rose-400 transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                {(!extractedData.mandatory_skills?.length) && (
                  <span className="text-slate-500 text-[11px] italic">No mandatory skills extracted — add them below</span>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newMandatorySkill}
                  onChange={(e) => setNewMandatorySkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddMandatorySkill())}
                  placeholder="Add missing mandatory skill and press Enter..."
                  className="flex-1 p-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-blue-500"
                />
                <button type="button" onClick={handleAddMandatorySkill} className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold flex items-center space-x-1 transition-colors">
                  <Plus className="w-3.5 h-3.5" /><span>Add</span>
                </button>
              </div>
            </div>

            {/* Nice-to-Have Skills */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-purple-900/50">
              <label className="block text-purple-300 font-bold mb-2">
                🟣 Nice-to-Have Skills (Preferred) — {extractedData.good_to_have_skills?.length || 0} extracted
              </label>
              <div className="flex flex-wrap gap-1.5 mb-2.5 max-h-24 overflow-y-auto">
                {(extractedData.good_to_have_skills || []).map((s, i) => (
                  <span key={i} className="inline-flex items-center px-2.5 py-1 rounded-lg bg-purple-950/80 text-purple-300 border border-purple-700/60 font-semibold text-[11px]">
                    {s.name}
                    <button onClick={() => handleRemoveGoodSkill(i)} className="ml-1.5 text-purple-400/60 hover:text-rose-400 transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newGoodSkill}
                  onChange={(e) => setNewGoodSkill(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddGoodSkill())}
                  placeholder="Add preferred skill and press Enter..."
                  className="flex-1 p-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-purple-500"
                />
                <button type="button" onClick={handleAddGoodSkill} className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold flex items-center space-x-1 transition-colors">
                  <Plus className="w-3.5 h-3.5" /><span>Add</span>
                </button>
              </div>
            </div>

            {/* Responsibilities */}
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-700/50">
              <label className="flex items-center space-x-1.5 text-slate-300 font-bold mb-2">
                <ClipboardList className="w-3.5 h-3.5" />
                <span>Key Responsibilities — {extractedData.responsibilities?.length || 0} extracted</span>
              </label>
              <div className="space-y-1.5 mb-2.5 max-h-32 overflow-y-auto">
                {(extractedData.responsibilities || []).map((r, i) => (
                  <div key={i} className="flex items-start space-x-2 p-2 rounded-lg bg-slate-950/80 border border-slate-800 text-slate-300 text-[11px]">
                    <span className="text-slate-500 shrink-0 mt-0.5">•</span>
                    <span className="flex-1">{r}</span>
                    <button onClick={() => handleRemoveResponsibility(i)} className="text-slate-600 hover:text-rose-400 shrink-0 transition-colors">
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
                {(!extractedData.responsibilities?.length) && (
                  <span className="text-slate-500 text-[11px] italic">No responsibilities extracted — add them below</span>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newResponsibility}
                  onChange={(e) => setNewResponsibility(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddResponsibility())}
                  placeholder="Add a key responsibility..."
                  className="flex-1 p-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-slate-500"
                />
                <button type="button" onClick={handleAddResponsibility} className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold flex items-center space-x-1 transition-colors">
                  <Plus className="w-3.5 h-3.5" /><span>Add</span>
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3 pt-2">
              <button
                onClick={() => setExtractedData(null)}
                className="w-1/3 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-semibold hover:bg-slate-700 text-xs transition-colors"
              >
                ← Back to JD
              </button>
              <button
                disabled={loading}
                onClick={handleSaveJob}
                className="w-2/3 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold text-xs hover:opacity-95 disabled:opacity-50 shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2 transition-opacity"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{loading ? 'Creating Job...' : 'Confirm & Create Job Posting'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
