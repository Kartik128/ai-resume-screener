import React, { useState } from 'react';
import { Sparkles, Upload, FileCheck } from 'lucide-react';
import api from '../services/api';

export default function ResumeUploadModal({ jobId, onClose, onUploaded }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!files.length) return;
    setLoading(true);
    try {
      const formData = new FormData();
      if (jobId) formData.append('job_id', jobId);

      if (files.length === 1) {
        formData.append('file', files[0]);
        await api.post('/resumes/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else {
        files.forEach((f) => formData.append('files', f));
        const res = await api.post('/resumes/bulk-upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        setResult(res.data);
      }
      onUploaded();
      if (files.length === 1) onClose();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg p-6 rounded-2xl border border-slate-700 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <h3 className="font-heading font-bold text-lg text-white flex items-center">
            <Upload className="w-5 h-5 text-blue-400 mr-2" />
            Upload Candidate Resumes
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white font-bold text-lg">✕</button>
        </div>

        {!result ? (
          <div className="mt-4 space-y-4">
            <div className="p-8 border-2 border-dashed border-slate-800 hover:border-blue-500 rounded-xl text-center">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.txt"
                onChange={(e) => setFiles(Array.from(e.target.files))}
                className="hidden"
                id="resume-upload-input"
              />
              <label htmlFor="resume-upload-input" className="cursor-pointer space-y-2 block">
                <Upload className="w-8 h-8 text-blue-400 mx-auto" />
                <p className="text-xs text-slate-300 font-medium">Drag & Drop or click to upload PDF, DOCX, Images</p>
                <p className="text-[10px] text-slate-500">Supports Bulk Upload (Up to 50 files)</p>
              </label>
            </div>

            {files.length > 0 && (
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <span className="font-bold text-blue-400">{files.length} File(s) Selected:</span>
                <ul className="mt-1 space-y-0.5 text-slate-400 max-h-24 overflow-y-auto">
                  {files.map((f, i) => (
                    <li key={i} className="truncate">• {f.name}</li>
                  ))}
                </ul>
              </div>
            )}

            <button
              disabled={loading || files.length === 0}
              onClick={handleUpload}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold text-xs hover:opacity-95 disabled:opacity-50 flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/20"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'AI Extracting & Scoring...' : `Ingest & Parse ${files.length} Resume(s)`}</span>
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-4 text-center">
            <FileCheck className="w-12 h-12 text-emerald-400 mx-auto" />
            <h4 className="text-base font-bold text-white">Bulk Ingestion Complete!</h4>
            <p className="text-xs text-slate-300">
              Successfully processed <span className="font-bold text-emerald-400">{result.successful_count}</span> out of {result.total_uploaded} resumes.
            </p>
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-blue-600 text-white font-semibold text-xs hover:bg-blue-500"
            >
              Done & View Leaderboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
