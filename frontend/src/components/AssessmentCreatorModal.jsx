import React, { useState } from 'react';
import { X, Plus, Trash2, Save, BookOpen } from 'lucide-react';
import api from '../services/api';

export default function AssessmentCreatorModal({ jobId, jobTitle, onClose }) {
  const [questions, setQuestions] = useState([
    {
      question_text: '',
      choices: [
        { choice_text: '', is_correct: false },
        { choice_text: '', is_correct: false }
      ]
    }
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [bulkText, setBulkText] = useState('');
  const [showBulkImport, setShowBulkImport] = useState(false);

  const handleBulkImport = () => {
    if (!bulkText.trim()) return;
    try {
      // Split by double newlines to isolate questions block
      const questionBlocks = bulkText.split(/\n\n+/);
      const parsedQuestions = [];

      for (const block of questionBlocks) {
        const lines = block.split('\n').map(l => l.trim()).filter(Boolean);
        if (lines.length < 3) continue;

        // Line 1 is the question
        const questionText = lines[0].replace(/^Q\d+[:.]?\s*/i, '');
        const choices = [];

        // Remaining lines are choice options
        for (let i = 1; i < lines.length; i++) {
          const rawChoice = lines[i];
          const isCorrect = rawChoice.startsWith('*') || rawChoice.endsWith('*');
          const choiceText = rawChoice.replace(/^\*\s*/, '').replace(/\*$/, '').replace(/^[a-eA-E][).]\s*/, '');
          choices.push({ choice_text: choiceText, is_correct: isCorrect });
        }

        // If no choice was explicitly marked, set first as correct fallback
        if (!choices.some(c => c.is_correct) && choices.length > 0) {
          choices[0].is_correct = true;
        }

        parsedQuestions.push({
          question_text: questionText,
          choices: choices
        });
      }

      if (parsedQuestions.length > 0) {
        setQuestions(parsedQuestions);
        setBulkText('');
        setShowBulkImport(false);
        setSuccess(`Successfully imported ${parsedQuestions.length} questions from text!`);
      } else {
        setError('No valid questions found. Check your formatting.');
      }
    } catch (e) {
      setError('Failed to parse text format. Ensure syntax matches guidelines.');
    }
  };

  const handleAddQuestion = () => {
    setQuestions([
      ...questions,
      {
        question_text: '',
        choices: [
          { choice_text: '', is_correct: false },
          { choice_text: '', is_correct: false }
        ]
      }
    ]);
  };

  const handleRemoveQuestion = (idx) => {
    setQuestions(questions.filter((_, i) => i !== idx));
  };

  const handleAddChoice = (qIdx) => {
    const updated = [...questions];
    updated[qIdx].choices.push({ choice_text: '', is_correct: false });
    setQuestions(updated);
  };

  const handleRemoveChoice = (qIdx, cIdx) => {
    const updated = [...questions];
    updated[qIdx].choices = updated[qIdx].choices.filter((_, i) => i !== cIdx);
    setQuestions(updated);
  };

  const handleSave = async () => {
    // Validate
    for (const q of questions) {
      if (!q.question_text.trim()) {
        setError('All questions must have question text.');
        return;
      }
      const correct = q.choices.filter(c => c.is_correct);
      if (correct.length !== 1) {
        setError('Each question must have exactly one correct choice selected.');
        return;
      }
      for (const c of q.choices) {
        if (!c.choice_text.trim()) {
          setError('All choices must have text values filled in.');
          return;
        }
      }
    }

    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await api.post('/assessments/', {
        job_id: jobId,
        title: `Validation test for ${jobTitle}`,
        questions: questions,
        time_limit_mins: 15
      });
      setSuccess('Skills validation assessment created successfully!');
      setTimeout(() => onClose(), 1500);
    } catch (e) {
      setError('Failed to save assessment checklist.');
    }
    setSubmitting(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="glass-card w-full max-w-2xl rounded-2xl border border-slate-700/60 shadow-2xl flex flex-col" style={{ maxHeight: '90vh' }}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 shrink-0">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-emerald-400" />
            <div>
              <h2 className="font-heading font-bold text-white text-base leading-tight">Skills Validation Test Creator</h2>
              <p className="text-xs text-slate-400">{jobTitle}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Builder */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div className="flex justify-end shrink-0">
            <button
              type="button"
              onClick={() => setShowBulkImport(!showBulkImport)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px] font-bold transition-all"
            >
              {showBulkImport ? 'Cancel Import' : '⚡ Bulk Copy-Paste Import'}
            </button>
          </div>

          {showBulkImport && (
            <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-800/35 space-y-3">
              <label className="block text-xs font-semibold text-purple-300">Copy-Paste Structured Questions</label>
              <p className="text-[10px] text-slate-400">Format: Separate questions with double spacing. Prefix correct answers with an asterisk (*).</p>
              <pre className="text-[9px] bg-slate-950 p-2.5 rounded border border-slate-850 text-slate-450 leading-relaxed">
{`Q1. Which of the following is correct about Python?
A. It is compiled
*B. It is interpreted
C. It is low level`}
              </pre>
              <textarea
                rows={5}
                value={bulkText}
                onChange={(e) => setBulkText(e.target.value)}
                placeholder="Paste questions here..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
              />
              <button
                type="button"
                onClick={handleBulkImport}
                className="w-full py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs"
              >
                Import Questions
              </button>
            </div>
          )}

          {error && <div className="p-3 bg-rose-950/20 border border-rose-900/40 text-rose-300 text-xs rounded-xl">{error}</div>}
          {success && <div className="p-3 bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 text-xs rounded-xl">{success}</div>}

          {questions.map((q, qIdx) => (
            <div key={qIdx} className="p-4 rounded-xl bg-slate-900/30 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-350 text-xs">Question #{qIdx + 1}</span>
                {questions.length > 1 && (
                  <button onClick={() => handleRemoveQuestion(qIdx)} className="text-rose-400 hover:text-rose-300 p-1.5 rounded-lg hover:bg-rose-950/20 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Question Content *</label>
                <input
                  type="text"
                  placeholder="e.g. Which of the following is correct about Python variables?"
                  value={q.question_text}
                  onChange={(e) => {
                    const updated = [...questions];
                    updated[qIdx].question_text = e.target.value;
                    setQuestions(updated);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-[11px] text-slate-400">Multiple Choices * (select exact correct answer)</label>
                {q.choices.map((c, cIdx) => (
                  <div key={cIdx} className="flex items-center gap-2">
                    <input
                      type="radio"
                      name={`correct-choice-${qIdx}`}
                      checked={c.is_correct}
                      onChange={() => {
                        const updated = [...questions];
                        updated[qIdx].choices = updated[qIdx].choices.map((choice, i) => ({
                          ...choice,
                          is_correct: i === cIdx
                        }));
                        setQuestions(updated);
                      }}
                      className="accent-blue-500 cursor-pointer"
                    />
                    <input
                      type="text"
                      placeholder={`Choice #${cIdx + 1}`}
                      value={c.choice_text}
                      onChange={(e) => {
                        const updated = [...questions];
                        updated[qIdx].choices[cIdx].choice_text = e.target.value;
                        setQuestions(updated);
                      }}
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-650 focus:outline-none focus:border-blue-500"
                    />
                    {q.choices.length > 2 && (
                      <button onClick={() => handleRemoveChoice(qIdx, cIdx)} className="text-slate-500 hover:text-rose-400 transition-colors">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
                
                <button
                  onClick={() => handleAddChoice(qIdx)}
                  className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1.5 mt-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Choice</span>
                </button>
              </div>
            </div>
          ))}

          <button
            onClick={handleAddQuestion}
            className="w-full py-3 rounded-xl border border-dashed border-slate-750 hover:border-slate-600 text-xs font-semibold text-slate-400 hover:text-white flex items-center justify-center gap-1.5 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Validation Question</span>
          </button>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800 bg-slate-900/10 shrink-0 flex items-center justify-end">
          <button
            onClick={handleSave}
            disabled={submitting}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/25 transition-all"
          >
            {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save Assessment</span>
          </button>
        </div>

      </div>
    </div>
  );
}
