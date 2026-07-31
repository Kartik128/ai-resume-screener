import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import JobCreateModal from '../components/JobCreateModal';
import { Briefcase, Plus, MapPin, Sparkles } from 'lucide-react';
import api from '../services/api';

export default function Jobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showJobModal, setShowJobModal] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/jobs/');
      setJobs(res.data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between glass-panel p-6 rounded-3xl border border-slate-800">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Organization Postings</span>
            <h1 className="font-heading font-extrabold text-2xl text-white mt-1">Job Openings</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/jd-preparation')}
              className="px-4 py-2.5 rounded-xl border border-blue-500/40 bg-blue-950/20 hover:bg-blue-950/40 text-blue-300 text-xs font-semibold flex items-center space-x-2 transition-all"
            >
              <Sparkles className="w-4 h-4 text-blue-400 animate-pulse" />
              <span>AI JD Builder</span>
            </button>
            <button
              onClick={() => setShowJobModal(true)}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:opacity-95 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-blue-500/20"
            >
              <Plus className="w-4 h-4" />
              <span>Post New Job</span>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-xs">Loading Job Openings...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {jobs.map((job) => (
              <div key={job.id} className="glass-card p-5 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-950 text-blue-400 border border-blue-800">
                      {job.department || 'Engineering'}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                      {job.status}
                    </span>
                  </div>
                  <h3 className="font-heading font-bold text-lg text-white mt-2 leading-tight">{job.title}</h3>
                  <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                    <span>{job.min_experience_years || 0}+ Yrs Exp</span>
                    <span className="flex items-center"><MapPin className="w-3 h-3 mr-0.5" />{job.location || 'Remote'}</span>
                  </div>
                </div>

                <div>
                  <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Mandatory Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {job.job_skills?.filter((s) => s.is_mandatory).slice(0, 5).map((js) => (
                      <span key={js.id} className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 text-[10px] font-medium">
                        {js.skill?.name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showJobModal && <JobCreateModal onClose={() => setShowJobModal(false)} onCreated={fetchJobs} />}
    </div>
  );
}
