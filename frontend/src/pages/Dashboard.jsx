import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import CandidateCard from '../components/CandidateCard';
import CandidateComparisonModal from '../components/CandidateComparisonModal';
import ResumeUploadModal from '../components/ResumeUploadModal';
import JobCreateModal from '../components/JobCreateModal';
import { Sparkles, Plus, Upload, Download, Filter, Columns, RefreshCw } from 'lucide-react';
import api from '../services/api';

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Modals
  const [showJobModal, setShowJobModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [selectedForCompare, setSelectedForCompare] = useState([]);

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

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowJobModal(true)}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center space-x-2 border border-slate-700 transition-all"
            >
              <Plus className="w-4 h-4 text-blue-400" />
              <span>New Job</span>
            </button>

            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-blue-500/20 transition-all"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Resumes</span>
            </button>
          </div>
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
                <a
                  href={`/api/v1/exports/job/${selectedJobId}/csv`}
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 font-medium"
                >
                  CSV
                </a>
                <a
                  href={`/api/v1/exports/job/${selectedJobId}/excel`}
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 font-medium"
                >
                  Excel
                </a>
              </div>
            )}
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

        {/* Candidate Cards Grid */}
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs font-medium">Evaluating candidate scores...</div>
        ) : candidates.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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
    </div>
  );
}
