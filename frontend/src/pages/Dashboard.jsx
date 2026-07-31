import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import CandidateCard from '../components/CandidateCard';
import CandidateComparisonModal from '../components/CandidateComparisonModal';
import ResumeUploadModal from '../components/ResumeUploadModal';
import JobCreateModal from '../components/JobCreateModal';
import { Sparkles, Plus, Upload, Download, Filter, Columns, RefreshCw, LayoutGrid, List, RotateCw } from 'lucide-react';
import api from '../services/api';
import ScorecardEditorModal from '../components/ScorecardEditorModal';
import TalentRediscoveryModal from '../components/TalentRediscoveryModal';
import AssessmentCreatorModal from '../components/AssessmentCreatorModal';
import IntakeCopilotModal from '../components/IntakeCopilotModal';

import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Modals
  const [showJobModal, setShowJobModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [showScorecardModal, setShowScorecardModal] = useState(false);
  const [showRediscoverModal, setShowRediscoverModal] = useState(false);
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [showIntakeModal, setShowIntakeModal] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (selectedJobId) {
      fetchCandidates();
    }
  }, [selectedJobId, statusFilter]);

  const fetchJobs = async () => {
    try {
      const res = await api.get('/jobs/');
      setJobs(res.data);
      if (res.data.length > 0 && !selectedJobId) {
        setSelectedJobId(res.data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const url = statusFilter
        ? `/dashboard/job/${selectedJobId}/candidates?status=${statusFilter}`
        : `/dashboard/job/${selectedJobId}/candidates`;
      const res = await api.get(url);
      setCandidates(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const toggleSelectCompare = (candId) => {
    if (selectedForCompare.includes(candId)) {
      setSelectedForCompare(selectedForCompare.filter((id) => id !== candId));
    } else {
      if (selectedForCompare.length >= 5) return;
      setSelectedForCompare([...selectedForCompare, candId]);
    }
  };

  const currentJob = jobs.find((j) => j.id === selectedJobId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Top Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-3xl border border-slate-800">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Recruiter Workspace</span>
            <h1 className="font-heading font-extrabold text-2xl text-white mt-1">Candidate Screening & Ranking</h1>
          </div>

          {user?.role !== 'viewer' && (
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowJobModal(true)}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-2 border border-slate-700 transition-all"
              >
                <Plus className="w-4 h-4 text-blue-400" />
                <span>New Job</span>
              </button>

              {selectedJobId && (
                <button
                  onClick={() => setShowRediscoverModal(true)}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-2 border border-slate-700 transition-all"
                >
                  <RotateCw className="w-4 h-4 text-purple-400" />
                  <span>Rediscover Talent</span>
                </button>
              )}

              <button
                onClick={() => setShowUploadModal(true)}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-blue-500/20 transition-all"
              >
                <Upload className="w-4 h-4" />
                <span>Upload Resumes</span>
              </button>
            </div>
          )}
        </div>

        {/* Job Selector & Action Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-semibold text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none max-w-xs"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.job_skills?.length || 0} Skills)
                </option>
              ))}
            </select>

            <button
              onClick={fetchCandidates}
              className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {user?.role !== 'viewer' && selectedJobId && (
              <>
                <button
                  onClick={() => setShowScorecardModal(true)}
                  className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 hover:text-white font-semibold text-xs transition-colors"
                  title="Customize scoring weights scorecard"
                >
                  Configure Weights
                </button>

                <button
                  onClick={() => setShowAssessmentModal(true)}
                  className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-350 hover:text-white font-semibold text-xs transition-colors"
                  title="Create skills validation test micro-assessment"
                >
                  Create Test
                </button>

                <button
                  onClick={() => setShowIntakeModal(true)}
                  className="px-3.5 py-2.5 rounded-xl bg-indigo-950/20 border border-indigo-900/40 hover:bg-indigo-900/30 text-indigo-300 font-bold text-xs transition-all flex items-center gap-1.5"
                  title="Generate weight scorecards from intake chats"
                >
                  <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                  <span>HM Intake Copilot</span>
                </button>
              </>
            )}

            {currentJob?.blind_mode && (
              <span className="px-3 py-2 rounded-xl text-xs font-bold bg-purple-950/60 text-purple-300 border border-purple-800/40 flex items-center space-x-1.5" title="Demographic details are hidden to reduce bias">
                <span>🔒 Blind Mode Active</span>
              </span>
            )}
          </div>

          {/* Controls: Export & Side-by-Side Compare */}
          <div className="flex items-center space-x-3">
            {selectedForCompare.length >= 2 && (
              <button
                onClick={() => setShowCompareModal(true)}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold flex items-center space-x-2 shadow-lg shadow-purple-500/25"
              >
                <Columns className="w-4 h-4" />
                <span>Compare ({selectedForCompare.length})</span>
              </button>
            )}

            {selectedJobId && (
              <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
                <button
                  onClick={async () => {
                    try {
                      const res = await api.get(`/exports/job/${selectedJobId}/csv`, { responseType: 'blob' });
                      const url = window.URL.createObjectURL(new Blob([res.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', `candidates_export_${selectedJobId}.csv`);
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                    } catch (e) {
                      console.error('Failed to export CSV', e);
                    }
                  }}
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 font-medium"
                >
                  CSV
                </button>
                <button
                  onClick={async () => {
                    try {
                      const res = await api.get(`/exports/job/${selectedJobId}/excel`, { responseType: 'blob' });
                      const url = window.URL.createObjectURL(new Blob([res.data]));
                      const link = document.createElement('a');
                      link.href = url;
                      link.setAttribute('download', `candidates_export_${selectedJobId}.xlsx`);
                      document.body.appendChild(link);
                      link.click();
                      link.remove();
                    } catch (e) {
                      console.error('Failed to export Excel', e);
                    }
                  }}
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 font-medium"
                >
                  Excel
                </button>
              </div>
            )}

            {/* Grid / List Mode Switcher */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-all ${
                  viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-lg transition-all ${
                  viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Status Pipeline Filter Tabs */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1">
          {['', 'shortlisted', 'maybe', 'rejected'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold capitalize whitespace-nowrap transition-all ${
                statusFilter === st
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              {st || 'All Candidates'}
            </button>
          ))}
        </div>

        {/* Candidate Cards Grid / List view */}
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs font-medium">Evaluating candidate scores...</div>
        ) : candidates.length > 0 ? (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-5' : 'flex flex-col gap-4'}>
            {candidates.map((cand) => (
              <CandidateCard
                key={cand.candidate_id}
                candidate={cand}
                onStatusChange={fetchCandidates}
                isSelectedForCompare={selectedForCompare.includes(cand.candidate_id)}
                onToggleSelectCompare={toggleSelectCompare}
              />
            ))}
          </div>
        ) : (
          <div className="glass-panel p-16 rounded-3xl text-center space-y-3 border border-slate-800">
            <Sparkles className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="font-heading font-bold text-lg text-white">No candidates uploaded for this job yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Upload PDF or DOCX resumes to automatically parse profiles and run AI explainable scoring.
            </p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="mt-3 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20"
            >
              Upload Resumes Now
            </button>
          </div>
        )}
      </main>

      {/* Modals */}
      {showJobModal && <JobCreateModal onClose={() => setShowJobModal(false)} onCreated={fetchJobs} />}
      {showUploadModal && (
        <ResumeUploadModal
          jobId={selectedJobId}
          onClose={() => setShowUploadModal(false)}
          onUploaded={fetchCandidates}
        />
      )}
      {showCompareModal && (
        <CandidateComparisonModal
          jobId={selectedJobId}
          candidateIds={selectedForCompare}
          onClose={() => setShowCompareModal(false)}
        />
      )}
      {showScorecardModal && selectedJobId && (
        <ScorecardEditorModal
          jobId={selectedJobId}
          jobTitle={currentJob?.title || 'Job Posting'}
          onClose={() => setShowScorecardModal(false)}
          onSaved={fetchCandidates}
        />
      )}
      {showRediscoverModal && selectedJobId && (
        <TalentRediscoveryModal
          jobId={selectedJobId}
          jobTitle={currentJob?.title || 'Job Posting'}
          onClose={() => {
            setShowRediscoverModal(false);
            fetchCandidates();
          }}
        />
      )}
      {showAssessmentModal && selectedJobId && (
        <AssessmentCreatorModal
          jobId={selectedJobId}
          jobTitle={currentJob?.title || 'Job Posting'}
          onClose={() => setShowAssessmentModal(false)}
        />
      )}
      {showIntakeModal && selectedJobId && (
        <IntakeCopilotModal
          onClose={() => setShowIntakeModal(false)}
          onWeightsSuggested={async (weights) => {
            try {
              await api.post(`/scorecards/job/${selectedJobId}`, weights);
              fetchCandidates();
            } catch (err) {
              console.error('Failed to save intake scorecard weights overrides.', err);
            }
          }}
        />
      )}
    </div>
  );
}
