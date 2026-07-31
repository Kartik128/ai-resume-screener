import React, { useEffect, useState } from 'react';
import { X, Clock, MessageSquare, Tag, UserCheck, AlertTriangle, Sparkles, Plus, Loader2 } from 'lucide-react';
import api from '../services/api';
import OfferWorkflowModal from './OfferWorkflowModal';

export default function CandidateTimelineModal({ applicationId, candidateId, candidateName, onClose }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Audio Transcripts States
  const [transcriptProfile, setTranscriptProfile] = useState(null);
  const [uploadingAudio, setUploadingAudio] = useState(false);

  // Offer Workflow State
  const [showOfferModal, setShowOfferModal] = useState(false);

  // Drag and Drop Popup panel position state
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const loadHistory = async () => {
    try {
      const res = await api.get(`/pipeline/${applicationId}/history`);
      setActivities(res.data);
    } catch (e) {
      setError('Could not retrieve activity history.');
    }
    setLoading(false);
  };

  const loadTranscript = async () => {
    try {
      const res = await api.get(`/transcripts/candidate/${candidateId}`);
      if (res.data) {
        setTranscriptProfile(res.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleUploadAudio = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingAudio(true);
    setError('');
    const formData = new FormData();
    formData.append('candidate_id', candidateId);
    formData.append('job_id', 'bdbd8046-98fb-4cd8-b7d9-621049068f5c'); // mock job fallback
    formData.append('file', file);

    try {
      const res = await api.post('/transcripts/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setTranscriptProfile(res.data);
      setSuccess('Audio processed, transcribed, and aligned with scorecard!');
      await loadHistory();
    } catch (err) {
      setError('Failed to process interview transcript.');
    }
    setUploadingAudio(false);
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setSubmitting(true);
    try {
      await api.post(`/pipeline/${applicationId}/note`, { note: newNote });
      setNewNote('');
      setSuccess('Note added successfully!');
      await loadHistory();
    } catch (err) {
      setError('Failed to submit note.');
    }
    setSubmitting(false);
  };

  const handleClearHistory = async () => {
    setDeleting(true);
    try {
      await api.delete(`/pipeline/${applicationId}/history`);
      setSuccess('Activity history cleared successfully!');
      await loadHistory();
    } catch (err) {
      setError('Failed to clear activity history.');
    }
    setDeleting(false);
  };

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

  useEffect(() => {
    loadHistory();
    loadTranscript();
  }, [applicationId]);

  const getActivityIcon = (type) => {
    switch (type) {
      case 'stage_change':
        return <Clock className="w-4 h-4 text-blue-400" />;
      case 'note_added':
        return <MessageSquare className="w-4 h-4 text-emerald-400" />;
      case 'owner_assigned':
        return <UserCheck className="w-4 h-4 text-purple-400" />;
      case 'reminder_set':
        return <Clock className="w-4 h-4 text-amber-400" />;
      case 'identity_revealed':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'score_overridden':
        return <Sparkles className="w-4 h-4 text-indigo-400" />;
      default:
        return <MessageSquare className="w-4 h-4 text-slate-400" />;
    }
  };

  const formatStage = (val) => {
    if (!val) return '';
    return val.replace('_', ' ').toUpperCase();
  };

  const handleDeleteCandidate = async () => {
    if (!window.confirm(`WARNING: Wiping candidate records is permanent and cannot be undone.\n\nAre you sure you want to scrub all resume texts, scores, files, and timeline records for "${candidateName}" under GDPR regulations?`)) {
      return;
    }
    setDeleting(true);
    setError('');
    setSuccess('');
    try {
      await api.delete(`/resumes/candidate/${candidateId}`);
      setSuccess('Candidate scrubbed successfully! Refreshing dashboard...');
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (e) {
      setError('Failed to execute GDPR hard deletion.');
    }
    setDeleting(false);
  };

  return (
    <div className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-4 bg-slate-950/20 backdrop-blur-[2px]">
      <div 
        className="w-full max-w-lg rounded-2xl border border-emerald-500/40 bg-slate-900/95 backdrop-blur-xl shadow-[0_0_50px_-12px_rgba(16,185,129,0.3)] flex flex-col pointer-events-auto" 
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          maxHeight: '85vh',
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        
        {/* Drag-Header */}
        <div 
          onMouseDown={handleMouseDown}
          className="drag-header flex items-center justify-between px-6 py-4 border-b border-emerald-950/80 shrink-0 cursor-grab select-none bg-gradient-to-r from-emerald-950/65 to-slate-900/65 rounded-t-2xl"
        >
          <div>
            <h2 className="font-heading font-bold text-white text-base leading-tight flex items-center gap-1.5">
              <span className="text-emerald-300">Timeline & Activity History</span>
              <span className="text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800/40 px-1.5 py-0.5 rounded">Drag to Move</span>
            </h2>
            <p className="text-xs text-slate-350">{candidateName}</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Interview Intelligence Audio Transcript Section */}
        <div className="p-6 border-b border-slate-800/80 bg-purple-950/10 space-y-3 shrink-0">
          <div className="text-xs font-semibold text-purple-300 uppercase tracking-wider flex items-center gap-1">✨ Interview Intelligence (Zoom / Teams Transcripts)</div>
          
          {transcriptProfile ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-300 font-semibold">🎙️ Transcript Analysis Available</span>
                <span className="px-2 py-0.5 rounded bg-purple-900/50 border border-purple-800 text-[10px] text-purple-300 font-bold">Alignment Score: {transcriptProfile.alignment_score}%</span>
              </div>
              <div className="text-[10px] bg-slate-950/80 p-3 rounded-lg border border-slate-900 text-slate-400 space-y-1">
                <p className="font-bold text-slate-300">AI Summary & Scorecard Alignment Match:</p>
                <p className="italic">"{transcriptProfile.summary_analysis}"</p>
                <details className="mt-2 cursor-pointer">
                  <summary className="text-[9px] text-purple-400 hover:underline">View Raw Transcript Text</summary>
                  <pre className="mt-1.5 p-2 rounded bg-slate-900 border border-slate-850 text-[9px] font-mono text-slate-450 overflow-x-auto whitespace-pre-wrap max-h-32">
                    {transcriptProfile.raw_transcript}
                  </pre>
                </details>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-4">
              <p className="text-[10px] text-slate-400">No meeting recordings analyzed. Upload Zoom/Teams audio files to auto-transcribe & score.</p>
              <label className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-[10px] font-bold cursor-pointer transition-all shrink-0">
                {uploadingAudio ? 'Transcribing...' : 'Upload Recording'}
                <input
                  type="file"
                  accept=".mp3,.wav,.m4a,.mp4"
                  onChange={handleUploadAudio}
                  disabled={uploadingAudio}
                  className="hidden"
                />
              </label>
            </div>
          )}
        </div>

        {/* Note Editor */}
        <form onSubmit={handleAddNote} className="p-6 border-b border-slate-800/80 bg-slate-900/20 shrink-0 space-y-3">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Add Recruitment Note</div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Discussed salary expectations, candidate is looking for..."
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              disabled={submitting}
              className="flex-1 bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={submitting || !newNote.trim()}
              className="flex items-center justify-center p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 transition-colors"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            </button>
          </div>
        </form>

        {/* Timeline */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && <div className="p-3 mb-4 bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs rounded-xl">{error}</div>}
          {success && <div className="p-3 mb-4 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 text-xs rounded-xl">{success}</div>}

          {loading ? (
            <div className="flex justify-center items-center py-12"><Loader2 className="w-6 h-6 text-slate-400 animate-spin" /></div>
          ) : activities.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">No activity recorded yet.</div>
          ) : (
            <div className="relative border-l-2 border-slate-800/80 ml-2.5 pl-6 space-y-6">
              {activities.map((act) => (
                <div key={act.id} className="relative">
                  {/* Timeline point */}
                  <span className="absolute -left-9 top-0.5 flex items-center justify-center w-5 h-5 rounded-full bg-slate-950 border border-slate-850 ring-4 ring-slate-950">
                    {getActivityIcon(act.activity_type)}
                  </span>
                  
                  {/* Event Detail */}
                  <div className="text-sm">
                    <span className="text-xs text-slate-500 font-semibold block mb-0.5">
                      {new Date(act.created_at).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })} · by {act.actor_name}
                    </span>
                    <p className="text-slate-200">
                      {act.activity_type === 'stage_change' && (
                        <>
                          Moved from <span className="font-semibold text-slate-400">{formatStage(act.from_value)}</span> to <span className="font-semibold text-blue-400">{formatStage(act.to_value)}</span>
                        </>
                      )}
                      {act.activity_type === 'note_added' && act.note}
                      {act.activity_type === 'owner_assigned' && 'Assigned new candidate owner'}
                      {act.activity_type === 'reminder_set' && `Set follow-up reminder for ${new Date(act.to_value).toLocaleDateString()}`}
                      {act.activity_type === 'identity_revealed' && '🔒 Revealed candidate identity from blind mode'}
                      {act.activity_type === 'score_overridden' && 'Recruiter score override applied'}
                    </p>
                    {act.activity_type !== 'note_added' && act.note && (
                      <p className="mt-1 text-xs text-slate-400 bg-slate-900/50 p-2 rounded-lg border border-slate-800">{act.note}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* GDPR Deletion footer */}
        <div className="p-4 border-t border-slate-800/85 bg-slate-950 flex items-center justify-between shrink-0 rounded-b-2xl">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={async () => {
                try {
                  await api.post(`/pipeline/${applicationId}/background-check`);
                  loadHistory();
                } catch (e) {
                  setError('Failed to trigger background check.');
                }
              }}
              className="px-3 py-1.5 rounded-lg bg-indigo-950 text-indigo-300 hover:bg-indigo-900 border border-indigo-900/50 text-[10px] font-bold transition-all"
            >
              🛡️ Trigger Background Check
            </button>
            <button
              onClick={() => setShowOfferModal(true)}
              className="px-3 py-1.5 rounded-lg bg-blue-955 text-blue-300 hover:bg-blue-900 border border-blue-900/50 text-[10px] font-bold transition-all"
            >
              ✍️ Release Offer
            </button>
            <span className="text-[10px] text-slate-500 self-center">GDPR DPDP Right to Deletion ready</span>
          </div>
          <button
            onClick={handleDeleteCandidate}
            disabled={deleting}
            className="px-3 py-1.5 rounded-lg bg-rose-950/45 hover:bg-rose-900/60 disabled:opacity-55 text-rose-450 hover:text-rose-350 border border-rose-900/40 text-[10px] font-bold transition-all"
          >
            {deleting ? 'Scrubbing Record...' : 'Scrub Candidate Data'}
          </button>
        </div>
      </div>

      {showOfferModal && (
        <OfferWorkflowModal
          candidateId={candidateId}
          candidateName={candidateName}
          onClose={() => setShowOfferModal(false)}
          onReleased={() => loadHistory()}
        />
      )}
    </div>
  );
}
