'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Clock,
  Save,
  CheckCircle2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Code2,
  HelpCircle,
} from 'lucide-react';
import { AssessmentQuestion, AssessmentSummary, EvaluationResult } from '../../lib/types/assessment';
import { api } from '../../lib/api-client';

interface AssessmentRunnerProps {
  assessment: AssessmentSummary;
  questions: AssessmentQuestion[];
  attemptId: string;
  timeLimitMinutes?: number | null;
  initialAnswers?: Record<string, string | number | boolean>;
  onComplete: (result: EvaluationResult) => void;
}

export default function AssessmentRunner({
  assessment,
  questions,
  attemptId,
  timeLimitMinutes,
  initialAnswers = {},
  onComplete,
}: AssessmentRunnerProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | number | boolean>>(initialAnswers);
  const [secondsRemaining, setSecondsRemaining] = useState<number | null>(
    timeLimitMinutes ? timeLimitMinutes * 60 : null
  );
  const [autosaveStatus, setAutosaveStatus] = useState<string>('All drafts saved');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const activeQuestion = questions[currentIndex];
  const autosaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Autosave callback
  const triggerAutosave = useCallback(async (currentAnswers: Record<string, unknown>) => {
    try {
      setAutosaveStatus('Saving draft...');
      await api.autosaveAttempt(assessment.id, attemptId, currentAnswers);
      const now = new Date().toLocaleTimeString();
      setAutosaveStatus(`Draft saved at ${now}`);
    } catch {
      setAutosaveStatus('Autosave offline (answers kept locally)');
    }
  }, [assessment.id, attemptId]);

  // Update answer and debounce autosave
  const handleAnswerChange = (questionId: string, value: string | number | boolean) => {
    const updated = { ...answers, [questionId]: value };
    setAnswers(updated);

    if (autosaveTimerRef.current) {
      clearTimeout(autosaveTimerRef.current);
    }
    autosaveTimerRef.current = setTimeout(() => {
      triggerAutosave(updated);
    }, 2000);
  };

  // Submit attempt
  const handleSubmit = useCallback(async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const result = await api.submitAssessmentAttempt(assessment.id, attemptId, answers);
      onComplete(result);
    } catch (err: unknown) {
      const msg = (err as Error).message || 'Submission failed. Please try again.';
      setSubmitError(msg);
      setIsSubmitting(false);
      setShowConfirmModal(false);
    }
  }, [assessment.id, attemptId, answers, onComplete]);

  // Timer countdown
  useEffect(() => {
    if (secondsRemaining === null) return;
    if (secondsRemaining <= 0) {
      // Auto-submit on time expiry
      handleSubmit();
      return;
    }

    const timer = setInterval(() => {
      setSecondsRemaining((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [secondsRemaining, handleSubmit]);

  // Format seconds MM:SS
  const formatTimer = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const isLowTime = secondsRemaining !== null && secondsRemaining < 300; // < 5 mins

  return (
    <div
      className="mx-auto max-w-4xl rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
      data-testid="assessment-runner"
    >
      {/* Top Banner: Assessment Title, Timer, Autosave Indicator */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-slate-50/70 px-6 py-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">{assessment.title}</h2>
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
            <span>
              Question {currentIndex + 1} of {questions.length}
            </span>
            <span>•</span>
            <span>{assessment.total_points} total points</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Autosave Status */}
          <div
            className="flex items-center gap-1.5 text-xs text-slate-500 font-medium"
            data-testid="autosave-status"
          >
            <Save className="h-3.5 w-3.5 text-slate-400" />
            <span>{autosaveStatus}</span>
          </div>

          {/* Timer Countdown */}
          {secondsRemaining !== null && (
            <div
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-mono font-bold transition ${
                isLowTime
                  ? 'bg-rose-100 text-rose-700 animate-pulse'
                  : 'bg-slate-200/80 text-slate-800'
              }`}
              data-testid="timer-countdown"
            >
              <Clock className="h-3.5 w-3.5" />
              <span>{formatTimer(secondsRemaining)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Question Stepper Indicator */}
      <div className="flex border-b border-slate-100 bg-slate-50/30 px-6 py-2.5 gap-1.5 overflow-x-auto">
        {(Array.isArray(questions) ? questions : []).map((q, idx) => {
          const isAnswered = answers[q.id] !== undefined && answers[q.id] !== '';
          const isCurrent = idx === currentIndex;
          return (
            <button
              key={q.id}
              onClick={() => setCurrentIndex(idx)}
              className={`flex h-7 w-7 items-center justify-center rounded-md text-xs font-semibold transition ${
                isCurrent
                  ? 'bg-sky-600 text-white shadow-sm'
                  : isAnswered
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
              data-testid={`question-step-${idx}`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>

      {/* Main Question Display Area */}
      <div className="p-8">
        {activeQuestion ? (
          <div>
            <div className="flex items-center justify-between gap-2 mb-4">
              <span className="rounded bg-sky-50 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider text-sky-800">
                {activeQuestion.type.toUpperCase()}
              </span>
              <span className="text-xs font-medium text-slate-500">
                {activeQuestion.points} {activeQuestion.points === 1 ? 'point' : 'points'}
              </span>
            </div>

            <h3 className="text-lg font-medium text-slate-900 leading-relaxed mb-6">
              {activeQuestion.prompt}
            </h3>

            {/* MCQ Question Renderer */}
            {activeQuestion.type === 'mcq' && Array.isArray(activeQuestion.options) && (
              <div className="space-y-3" data-testid="mcq-options-group">
                {activeQuestion.options.map((option, optIdx) => {
                  const isSelected = answers[activeQuestion.id] === option;
                  return (
                    <label
                      key={optIdx}
                      className={`flex items-center gap-3 rounded-xl border p-4 cursor-pointer transition ${
                        isSelected
                          ? 'border-sky-500 bg-sky-50/50 text-sky-950 font-medium ring-1 ring-sky-500'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${activeQuestion.id}`}
                        value={option}
                        checked={isSelected}
                        onChange={() => handleAnswerChange(activeQuestion.id, option)}
                        className="h-4 w-4 text-sky-600 focus:ring-sky-500"
                        data-testid={`mcq-option-${optIdx}`}
                      />
                      <span className="text-sm">{option}</span>
                    </label>
                  );
                })}
              </div>
            )}

            {/* Boolean Question Renderer */}
            {activeQuestion.type === 'boolean' && (
              <div className="flex gap-4" data-testid="boolean-options-group">
                {['True', 'False'].map((val) => {
                  const isSelected = answers[activeQuestion.id] === val;
                  return (
                    <button
                      key={val}
                      type="button"
                      onClick={() => handleAnswerChange(activeQuestion.id, val)}
                      className={`flex-1 rounded-xl border p-4 text-sm font-semibold transition ${
                        isSelected
                          ? 'border-sky-500 bg-sky-50 text-sky-900 ring-1 ring-sky-500'
                          : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                      data-testid={`boolean-option-${val.toLowerCase()}`}
                    >
                      {val}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Numerical Question Renderer */}
            {activeQuestion.type === 'numerical' && (
              <div className="space-y-2" data-testid="numerical-input-group">
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    step="any"
                    value={(answers[activeQuestion.id] as string) || ''}
                    onChange={(e) => handleAnswerChange(activeQuestion.id, e.target.value)}
                    placeholder="Enter numerical answer"
                    className="w-64 rounded-xl border border-slate-300 p-3 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                    data-testid="numerical-answer-input"
                  />
                  {activeQuestion.unit && (
                    <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-700">
                      Units: {activeQuestion.unit}
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400">
                  Relative tolerance: ±{activeQuestion.tolerance_percent || 2}%
                </p>
              </div>
            )}

            {/* Subjective Question Renderer */}
            {activeQuestion.type === 'subjective' && (
              <div className="space-y-2" data-testid="subjective-input-group">
                <textarea
                  rows={6}
                  value={(answers[activeQuestion.id] as string) || ''}
                  onChange={(e) => handleAnswerChange(activeQuestion.id, e.target.value)}
                  placeholder="Explain your understanding and working in detail..."
                  className="w-full rounded-xl border border-slate-300 p-4 text-sm text-slate-800 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 leading-relaxed"
                  data-testid="subjective-answer-textarea"
                />
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Graded via multi-criterion rubrics & misconception detection</span>
                  <span>
                    Words:{' '}
                    {((answers[activeQuestion.id] as string) || '')
                      .trim()
                      .split(/\s+/)
                      .filter(Boolean).length}
                  </span>
                </div>
              </div>
            )}

            {/* Coding Question Renderer */}
            {activeQuestion.type === 'coding' && (
              <div className="space-y-2" data-testid="coding-input-group">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                  <span className="flex items-center gap-1 font-mono">
                    <Code2 className="h-3.5 w-3.5 text-sky-600" />
                    Language: {activeQuestion.language || 'python'}
                  </span>
                  <span>Auto-evaluated against test cases</span>
                </div>
                <textarea
                  rows={8}
                  value={
                    (answers[activeQuestion.id] as string) !== undefined
                      ? (answers[activeQuestion.id] as string)
                      : activeQuestion.starter_code || ''
                  }
                  onChange={(e) => handleAnswerChange(activeQuestion.id, e.target.value)}
                  className="w-full font-mono text-xs rounded-xl border border-slate-800 bg-slate-900 p-4 text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-400"
                  data-testid="coding-answer-editor"
                />
              </div>
            )}
          </div>
        ) : (
          <div>No questions found in this assessment.</div>
        )}

        {submitError && (
          <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{submitError}</span>
          </div>
        )}
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50/50 px-8 py-4">
        <button
          type="button"
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-30 transition"
          data-testid="prev-question-button"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Previous</span>
        </button>

        {currentIndex < questions.length - 1 ? (
          <button
            type="button"
            onClick={() => setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))}
            className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-5 py-2 text-xs font-semibold text-white hover:bg-sky-700 transition"
            data-testid="next-question-button"
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setShowConfirmModal(true)}
            className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-6 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition"
            data-testid="open-submit-modal-button"
          >
            <CheckCircle2 className="h-4 w-4" />
            <span>Submit Assessment</span>
          </button>
        )}
      </div>

      {/* Submit Confirmation Modal */}
      {showConfirmModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4"
          data-testid="submit-confirm-modal"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-3">
              <HelpCircle className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Ready to Submit?</h3>
            <p className="mt-2 text-xs text-slate-600 leading-relaxed">
              You have answered {Object.keys(answers).length} of {questions.length} questions. Once
              submitted, your answers will be evaluated and learning mastery recorded.
            </p>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                disabled={isSubmitting}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Continue Reviewing
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="rounded-lg bg-emerald-600 px-5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                data-testid="confirm-submit-button"
              >
                {isSubmitting ? 'Evaluating...' : 'Confirm Submission'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
