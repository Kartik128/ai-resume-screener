import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { BookOpen, Clock, Calendar, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import api from '../services/api';

export default function CandidatePortal() {
  const { assessmentId, candidateId } = useParams();
  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [activePortalTab, setActivePortalTab] = useState('test'); // 'test' | 'schedule'

  // Schedule States
  const [selectedSlot, setSelectedSlot] = useState('');
  const [schedulerSubmitting, setSchedulerSubmitting] = useState(false);
  const [schedulingSuccess, setSchedulingSuccess] = useState('');

  // Experience Feedback NPS States
  const [nps, setNps] = useState(0);
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleSubmitFeedback = async () => {
    if (nps === 0) return;
    setSubmittingFeedback(true);
    setError('');
    try {
      await api.post('/experience/submit', {
        candidate_id: candidateId,
        nps_score: nps,
        feedback_text: feedbackNotes
      });
      setFeedbackSubmitted(true);
    } catch (e) {
      setError('Failed to log experience feedback review.');
    }
    setSubmittingFeedback(false);
  };

  const mockSlots = [
    { value: '2026-07-23T10:00:00Z', label: 'Thursday, July 23 at 10:00 AM (GMT)' },
    { value: '2026-07-23T02:00:00Z', label: 'Thursday, July 23 at 2:00 PM (GMT)' },
    { value: '2026-07-24T11:00:00Z', label: 'Friday, July 24 at 11:00 AM (GMT)' },
    { value: '2026-07-24T03:00:00Z', label: 'Friday, July 24 at 3:00 PM (GMT)' },
  ];

  useEffect(() => {
    const fetchPublicAssessment = async () => {
      try {
        const res = await api.get(`/assessments/${assessmentId}/public`);
        setAssessment(res.data);
      } catch (e) {
        setError('Assessment could not be loaded or token has expired.');
      }
      setLoading(false);
    };
    if (assessmentId) {
      fetchPublicAssessment();
    } else {
      setLoading(false);
    }
  }, [assessmentId]);

  const handleSubmitTest = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/assessments/${assessmentId}/submit`, {
        candidate_id: candidateId,
        answers: answers
      });
      setSuccess('Your validation answers have been graded and submitted successfully! You may now schedule your interview.');
      setActivePortalTab('schedule');
    } catch (e) {
      setError('Failed to submit assessment answers.');
    }
    setSubmitting(false);
  };

  const handleScheduleSelf = async (e) => {
    e.preventDefault();
    if (!selectedSlot) {
      setError('Please choose a valid scheduling slot.');
      return;
    }
    setSchedulerSubmitting(true);
    setError('');
    try {
      await api.post(`/assessments/${assessmentId}/schedule-candidate`, {
        candidate_id: candidateId,
        scheduled_at: selectedSlot
      });
      setSchedulingSuccess('Interview successfully scheduled! Look out for your Google Calendar email invite.');
    } catch (e) {
      setError('Failed to schedule calendar slot.');
    }
    setSchedulerSubmitting(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400 text-xs">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-2" />
        <span>Loading Candidate Portal Session...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navigation Header */}
      <header className="glass-panel px-6 py-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-5 h-5 text-blue-500" />
          <span className="font-heading text-lg font-bold text-white">TalentAI Candidate Portal</span>
        </div>
      </header>

      <main className="flex-1 max-w-2xl w-full mx-auto p-6 space-y-6">
        
        {/* Navigation Tabs */}
        <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 gap-1 shrink-0">
          <button
            onClick={() => setActivePortalTab('test')}
            className={`flex-1 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
              activePortalTab === 'test' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Skills Validation Test</span>
          </button>
          <button
            onClick={() => setActivePortalTab('schedule')}
            className={`flex-1 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
              activePortalTab === 'schedule' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Schedule Interview</span>
          </button>
        </div>

        {/* Dynamic Panel */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
          {error && (
            <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs rounded-xl flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {activePortalTab === 'test' ? (
            success ? (
              <div className="text-center py-8 space-y-3">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
                <h2 className="font-heading font-bold text-white text-base">Test Submitted Successfully!</h2>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">{success}</p>
                <button
                  onClick={() => setActivePortalTab('schedule')}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold"
                >
                  Schedule Your Interview
                </button>
              </div>
            ) : !assessment ? (
              <div className="text-center py-12 text-slate-500 text-xs">
                No active assessment found for this portal link.
              </div>
            ) : (
              <form onSubmit={handleSubmitTest} className="space-y-6">
                <div>
                  <h2 className="font-heading font-bold text-white text-lg">{assessment.title}</h2>
                  <div className="flex gap-4 text-[10px] text-slate-400 mt-1.5">
                    <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-blue-400" />Time Limit: {assessment.time_limit_mins} mins</span>
                    <span className="flex items-center gap-1"><BookOpen className="w-3.5 h-3.5 text-emerald-400" />Questions: {assessment.questions?.length}</span>
                  </div>
                </div>

                <div className="space-y-4 border-t border-slate-800/80 pt-4">
                  {assessment.questions.map((q, qIdx) => (
                    <div key={qIdx} className="p-4 rounded-xl bg-slate-900/40 border border-slate-850 space-y-3">
                      <div className="font-semibold text-white text-xs">Q{qIdx + 1}: {q.question_text}</div>
                      <div className="space-y-2">
                        {q.choices.map((choice, cIdx) => (
                          <label key={cIdx} className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-800 bg-slate-950/30 hover:bg-slate-900/30 cursor-pointer transition-colors text-xs text-slate-300">
                            <input
                              type="radio"
                              name={`question-${qIdx}`}
                              required
                              checked={answers[qIdx] === cIdx}
                              onChange={() => {
                                setAnswers({
                                  ...answers,
                                  [qIdx]: cIdx
                                });
                              }}
                              className="accent-blue-500"
                            />
                            <span>{choice}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/25 transition-all text-xs"
                >
                  {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Submit Validation Test</span>
                </button>
              </form>
            )
          ) : (
            schedulingSuccess ? (
              <div className="text-center py-8 space-y-4">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
                <h2 className="font-heading font-bold text-white text-base">Interview Scheduled!</h2>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">{schedulingSuccess}</p>
                
                {/* Candidate Feedback NPS Panel */}
                <div className="mt-6 p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-left space-y-3">
                  <span className="text-[11px] font-bold text-slate-350 block">Help us improve: Rate your application experience?</span>
                  
                  {feedbackSubmitted ? (
                    <p className="text-[10px] text-emerald-400 font-medium">Thank you! Your feedback has been received.</p>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex justify-between gap-1">
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(score => (
                          <button
                            key={score}
                            type="button"
                            onClick={() => setNps(score)}
                            className={`w-7 h-7 rounded text-[10px] font-bold transition-all border ${
                              nps === score
                                ? 'bg-blue-600 border-blue-500 text-white'
                                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                            }`}
                          >
                            {score}
                          </button>
                        ))}
                      </div>
                      <input
                        type="text"
                        placeholder="Any additional feedback or comments?"
                        value={feedbackNotes}
                        onChange={(e) => setFeedbackNotes(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[10px] text-white focus:outline-none focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onClick={handleSubmitFeedback}
                        disabled={submittingFeedback || nps === 0}
                        className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded font-bold text-[10px]"
                      >
                        Submit Experience Review
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <form onSubmit={handleScheduleSelf} className="space-y-6">
                <div>
                  <h2 className="font-heading font-bold text-white text-lg">Self-Schedule Interview</h2>
                  <p className="text-xs text-slate-400 mt-1">Select an available panel slot that works best for your schedule.</p>
                </div>

                <div className="space-y-3 border-t border-slate-800/80 pt-4">
                  {mockSlots.map((slot, idx) => (
                    <label key={idx} className="flex items-center gap-2.5 p-3 rounded-xl border border-slate-800 bg-slate-950/30 hover:bg-slate-900/30 cursor-pointer transition-colors text-xs text-slate-200">
                      <input
                        type="radio"
                        name="self-schedule-slot"
                        required
                        value={slot.value}
                        checked={selectedSlot === slot.value}
                        onChange={(e) => setSelectedSlot(e.target.value)}
                        className="accent-blue-500"
                      />
                      <span>{slot.label}</span>
                    </label>
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={schedulerSubmitting}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold flex items-center justify-center gap-1.5 shadow-lg shadow-blue-500/25 transition-all text-xs"
                >
                  {schedulerSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Confirm Scheduled Slot</span>
                </button>
              </form>
            )
          )}
        </div>
      </main>
    </div>
  );
}
