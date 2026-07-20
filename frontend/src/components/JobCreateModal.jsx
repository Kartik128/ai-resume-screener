import React, { useState } from 'react';
import { Sparkles, Upload, FileText } from 'lucide-react';
import api from '../services/api';

export default function JobCreateModal({ onClose, onCreated }) {
  const [activeTab, setActiveTab] = useState('paste'); // 'paste' | 'upload'
  const [rawText, setRawText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);

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
    }
    setLoading(false);
  };

  const handleSaveJob = async () => {
    setLoading(true);
    try {
      const payload = {
        title: extractedData.role,
        department: extractedData.department || 'Engineering',
        raw_description: rawText || 'Job description document uploaded.',
        status: 'active',
        min_experience_years: extractedData.min_experience_years,
        max_experience_years: extractedData.max_experience_years,
        education_requirement: extractedData.education_requirement,
        location: extractedData.location,
        is_remote: extractedData.is_remote,
        min_salary: extractedData.min_salary,
        max_salary: extractedData.max_salary,
        salary_currency: extractedData.salary_currency,
        responsibilities: extractedData.responsibilities,
        mandatory_skills: extractedData.mandatory_skills,
        good_to_have_skills: extractedData.good_to_have_skills,
      };
      await api.post('/jobs/', payload);
      onCreated();
      onClose();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-2xl p-6 rounded-2xl max-h-[90vh] overflow-y-auto border border-slate-700 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <h3 className="font-heading font-bold text-xl text-white flex items-center">
            <Sparkles className="w-5 h-5 text-blue-400 mr-2" />
            Create Job Description
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
        </div>

        {!extractedData ? (
          <div className="mt-4 space-y-4">
            {/* Tabs */}
            <div className="flex space-x-2 border-b border-slate-800 pb-2">
              <button
                onClick={() => setActiveTab('paste')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 ${
                  activeTab === 'paste' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <FileText className="w-4 h-4" />
                <span>Paste JD Text</span>
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 ${
                  activeTab === 'upload' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Upload className="w-4 h-4" />
                <span>Upload Document (PDF/DOCX)</span>
              </button>
            </div>

            {activeTab === 'paste' ? (
              <textarea
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste full Job Description text here..."
                rows={8}
                className="w-full p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            ) : (
              <div className="p-8 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl text-center">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="hidden"
                  id="jd-upload-input"
                />
                <label htmlFor="jd-upload-input" className="cursor-pointer space-y-2">
                  <Upload className="w-8 h-8 text-blue-400 mx-auto" />
                  <p className="text-xs text-slate-300 font-medium">Click to select PDF or DOCX file</p>
                  {file && <p className="text-xs text-emerald-400 font-bold">{file.name}</p>}
                </label>
              </div>
            )}

            <button
              disabled={loading || (activeTab === 'paste' ? !rawText : !file)}
              onClick={handleParse}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold text-xs hover:opacity-95 disabled:opacity-50 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'AI Extracting Requirements...' : 'Convert to Structured AI JSON'}</span>
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            <h4 className="text-xs font-bold uppercase text-blue-400 tracking-wider">AI Extracted Job Preview</h4>
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs space-y-3">
              <div>
                <span className="text-slate-500 font-semibold">Role Title: </span>
                <span className="text-white font-bold text-sm">{extractedData.role}</span>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Required Experience: </span>
                <span className="text-slate-200">{extractedData.min_experience_years} - {extractedData.max_experience_years} Years</span>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Mandatory Skills: </span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {extractedData.mandatory_skills.map((s, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 text-[10px] font-bold">
                      {s.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex space-x-3 pt-2">
              <button
                onClick={() => setExtractedData(null)}
                className="w-1/2 py-2.5 rounded-xl bg-slate-800 text-slate-300 font-semibold text-xs hover:bg-slate-700"
              >
                Back to Edit
              </button>
              <button
                disabled={loading}
                onClick={handleSaveJob}
                className="w-1/2 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-500 shadow-lg shadow-emerald-500/20"
              >
                Save Job Posting
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
