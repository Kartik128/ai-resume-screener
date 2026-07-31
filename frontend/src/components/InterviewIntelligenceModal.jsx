import React, { useState, useEffect } from 'react';
import { X, Mic, Upload, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import api from '../services/api';

export default function InterviewIntelligenceModal({ candidateId, jobId, candidateName, onClose }) {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    const fetchTranscript = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await api.get(`/transcripts/candidate/${candidateId}`);
        if (res.data) {
          setTranscript(res.data);
        }
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };
    fetchTranscript();
  }, [candidateId]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      const name = file.name.toLowerCase();
      if (name.endsWith('.mp3') || name.endsWith('.wav') || name.endsWith('.m4a') || name.endsWith('.mp4')) {
        setSelectedFile(file);
      } else {
        setError('Unsupported format. Provide MP3, WAV, or M4A.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const name = file.name.toLowerCase();
      if (name.endsWith('.mp3') || name.endsWith('.wav') || name.endsWith('.m4a') || name.endsWith('.mp4')) {
        setSelectedFile(file);
      } else {
        setError('Unsupported format. Provide MP3, WAV, or M4A.');
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('candidate_id', candidateId);
    formData.append('job_id', jobId);

    try {
      const res = await api.post('/transcripts/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setTranscript(res.data);
      setSelectedFile(null);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to upload and transcribe audio.');
    }
    setUploading(false);
  };

  // Drag and Drop Popup panel position state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e) => {
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

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div 
        className="w-full max-w-2xl rounded-2xl border border-cyan-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(6,182,212,0.3)] flex flex-col pointer-events-auto" 
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          maxHeight: '80vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        {/* Drag-Header */}
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-cyan-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-cyan-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight flex items-center gap-1.5">
              <span className="text-cyan-300">🎙️ Interview Intelligence</span>
              <span className="text-[9px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
            </h2>
            <p className="text-xs text-slate-350">AI audio transcription and scorecard matching — {candidateName}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs">
          {error && (
            <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 rounded-xl flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-450" />{error}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
          ) : !transcript ? (
            /* Upload Panel */
            <div className="space-y-4">
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`p-10 rounded-2xl border-2 border-dashed text-center transition-all cursor-pointer ${
                  dragOver
                    ? 'border-blue-500 bg-blue-950/15'
                    : 'border-slate-800 bg-slate-900/20 hover:border-slate-750 hover:bg-slate-900/40'
                }`}
              >
                <input
                  type="file"
                  accept=".mp3,.wav,.m4a,.mp4"
                  onChange={handleFileChange}
                  className="hidden"
                  id="audio-upload-input"
                />
                <label htmlFor="audio-upload-input" className="cursor-pointer space-y-3 block">
                  <div className="mx-auto w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
                    <Mic className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-slate-200 font-semibold">Drop Zoom/Teams audio recording or click to browse</p>
                    <p className="text-slate-500 text-[10px] mt-1">Supports MP3, WAV, M4A up to 50MB</p>
                  </div>
                </label>
              </div>

              {selectedFile && (
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                  <span className="text-slate-300 truncate font-mono">{selectedFile.name}</span>
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg font-bold flex items-center gap-1.5 transition-all"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Analyzing...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-3.5 h-3.5" />
                        <span>Analyze Recording</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Results Panel */
            <div className="space-y-5">
              {/* Score Indicator */}
              <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80">
                <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] mb-2">Scorecard Alignment</div>
                <div className={`w-24 h-24 rounded-full border-4 flex items-center justify-center font-heading font-extrabold text-2xl ${
                  transcript.alignment_score >= 80
                    ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/5'
                    : transcript.alignment_score >= 65
                    ? 'border-amber-500/30 text-amber-400 bg-amber-500/5'
                    : 'border-rose-500/30 text-rose-400 bg-rose-500/5'
                }`}>
                  {transcript.alignment_score}%
                </div>
                <p className="text-slate-500 text-[10px] mt-2">Semantic analysis of candidate statements compared to job criteria</p>
              </div>

              {/* AI Summary */}
              <div className="space-y-1.5">
                <h3 className="text-slate-300 font-bold uppercase tracking-wider text-[10px]">AI Interview Summary</h3>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-300 leading-relaxed">
                  {transcript.summary_analysis}
                </div>
              </div>

              {/* Full Transcript Monospace */}
              <details className="group border border-slate-800 rounded-xl overflow-hidden">
                <summary className="flex items-center justify-between px-4 py-3 bg-slate-900/40 cursor-pointer font-bold text-slate-400 select-none hover:text-slate-200">
                  <span>View Full Transcript</span>
                  <span className="text-[10px] group-open:rotate-180 transition-transform">▼</span>
                </summary>
                <div className="p-4 bg-slate-950 border-t border-slate-800 font-mono text-[11px] text-slate-400 whitespace-pre-wrap max-h-56 overflow-y-auto leading-relaxed">
                  {transcript.raw_transcript}
                </div>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
