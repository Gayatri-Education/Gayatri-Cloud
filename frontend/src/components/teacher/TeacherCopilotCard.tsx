'use client';

import React, { useState } from 'react';
import { CopilotBriefing } from '../../lib/types/teacher';
import { Sparkles, Check, AlertCircle, ArrowRight, ShieldAlert } from 'lucide-react';

interface TeacherCopilotCardProps {
  briefing: CopilotBriefing;
  onApplyAction?: (actionText: string) => Promise<void>;
}

export default function TeacherCopilotCard({
  briefing,
  onApplyAction,
}: TeacherCopilotCardProps) {
  const [appliedActions, setAppliedActions] = useState<string[]>([]);
  const [isApplying, setIsApplying] = useState(false);

  const handleApply = async (action: string) => {
    if (!onApplyAction) return;
    try {
      setIsApplying(true);
      await onApplyAction(action);
      setAppliedActions((prev) => [...prev, action]);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to apply action');
    } finally {
      setIsApplying(false);
    }
  };

  const confidencePct = Math.round(briefing.confidence_score * 100);

  return (
    <div
      className="rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50/50 via-white to-indigo-50/30 p-5 sm:p-6 shadow-sm space-y-5"
      data-testid="copilot-card"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-600 text-white shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Teacher Copilot — Pedagogical Briefing
            </h3>
            <p className="text-xs text-slate-500">
              Diagnostic recommendations grounded in real-time student interaction logs
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-600">Model Confidence:</span>
          <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-bold text-sky-800" data-testid="confidence-badge">
            {confidencePct}%
          </span>
        </div>
      </div>

      {/* Briefing Summary */}
      <div className="rounded-xl border border-sky-100 bg-white p-4 shadow-xs">
        <p className="text-sm text-slate-800 leading-relaxed font-normal" data-testid="briefing-summary">
          {briefing.summary}
        </p>
      </div>

      {/* Uncertainty & Confirmation Requirement Notice */}
      <div className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900" data-testid="uncertainty-notice">
        <ShieldAlert className="h-4 w-4 shrink-0 text-amber-700 mt-0.5" />
        <div>
          <strong>Grounding & Ethics Protocol:</strong> {briefing.uncertainty_note}
          {briefing.requires_teacher_confirmation && (
            <span className="block mt-1 font-semibold text-amber-800">
              Teacher review and explicit confirmation is required before any automatic tutor behavior adjustments take effect.
            </span>
          )}
        </div>
      </div>

      {/* Grid: Evidence Sources & Suggested Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Evidence Sources */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Verifiable Evidence Sources ({briefing.evidence_sources.length})
          </h4>
          <ul className="space-y-1.5" data-testid="evidence-sources-list">
            {briefing.evidence_sources.map((src, i) => (
              <li
                key={i}
                className="flex items-center gap-2 text-xs text-slate-700 rounded-lg bg-slate-50 border border-slate-200/60 px-2.5 py-1.5"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-sky-500 shrink-0" />
                <span className="truncate">{src}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Suggested Pedagogical Actions */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Recommended Interventions
          </h4>
          <div className="space-y-2" data-testid="suggested-actions-list">
            {briefing.suggested_actions.map((act, i) => {
              const isApplied = appliedActions.includes(act);
              return (
                <div
                  key={i}
                  className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 bg-white p-2.5 shadow-2xs"
                >
                  <span className="text-xs text-slate-800 leading-snug">{act}</span>
                  {onApplyAction && (
                    <button
                      onClick={() => handleApply(act)}
                      disabled={isApplying || isApplied}
                      className={`inline-flex shrink-0 items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition ${
                        isApplied
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-50'
                      }`}
                      data-testid={`apply-action-btn-${i}`}
                    >
                      {isApplied ? (
                        <>
                          <Check className="h-3.5 w-3.5" />
                          <span>Applied</span>
                        </>
                      ) : (
                        <>
                          <span>Apply</span>
                          <ArrowRight className="h-3 w-3" />
                        </>
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
