'use client';

import React, { useState } from 'react';
import { TeacherInstructionItem } from '../../lib/types/teacher';
import EmptyState from '../common/EmptyState';
import { Sliders, Plus, Trash2, ShieldCheck, Zap } from 'lucide-react';

interface InstructionEditorProps {
  courseId: string;
  instructions: TeacherInstructionItem[];
  onCreateInstruction?: (data: {
    tier: 'ORG' | 'COURSE' | 'CLASS' | 'STUDENT' | 'SESSION';
    directive_text: string;
    priority: number;
  }) => Promise<void>;
  onDeactivateInstruction?: (instructionId: string) => Promise<void>;
}

export default function InstructionEditor({
  courseId,
  instructions,
  onCreateInstruction,
  onDeactivateInstruction,
}: InstructionEditorProps) {
  const safeInstructions = Array.isArray(instructions) ? instructions : [];
  const [tier, setTier] = useState<'ORG' | 'COURSE' | 'CLASS' | 'STUDENT' | 'SESSION'>('COURSE');
  const [directiveText, setDirectiveText] = useState('');
  const [priority, setPriority] = useState<number>(3);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!directiveText.trim() || !onCreateInstruction) return;

    try {
      setIsSubmitting(true);
      setStatusMessage(null);
      await onCreateInstruction({
        tier,
        directive_text: directiveText.trim(),
        priority,
      });
      setDirectiveText('');
      setPriority(3);
      setStatusMessage('Pedagogical directive created and applied to AI tutor cascade.');
    } catch (err: unknown) {
      setStatusMessage(err instanceof Error ? err.message : 'Failed to create directive');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeactivate = async (id: string) => {
    if (!onDeactivateInstruction) return;
    try {
      await onDeactivateInstruction(id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to deactivate directive');
    }
  };

  const getTierColor = (t: string) => {
    switch (t) {
      case 'ORG':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'COURSE':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'CLASS':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'STUDENT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'SESSION':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6" data-testid="instruction-editor">
      {/* Directive Creator Form */}
      {onCreateInstruction && (
        <form
          onSubmit={handleSubmit}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-4"
          data-testid="instruction-form"
        >
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Sliders className="h-5 w-5 text-sky-600" />
            <h3 className="text-base font-semibold text-slate-900">
              Add Pedagogical Directive (5-Tier Cascade)
            </h3>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Cascade Tier
              </label>
              <select
                value={tier}
                onChange={(e) =>
                  setTier(e.target.value as 'ORG' | 'COURSE' | 'CLASS' | 'STUDENT' | 'SESSION')
                }
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                data-testid="tier-select"
              >
                <option value="COURSE">Course Tier (Applies to all sessions in course)</option>
                <option value="CLASS">Class Tier (Applies to specific cohort)</option>
                <option value="STUDENT">Student Tier (Personalized for struggling learner)</option>
                <option value="SESSION">Session Tier (Single-turn constraint)</option>
                <option value="ORG">Organization Tier (Institution-wide policy)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Priority Level (1 = Low, 5 = Critical Override)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value, 10))}
                  className="w-full accent-sky-600"
                  data-testid="priority-slider"
                />
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 font-bold text-sky-700 text-sm">
                  {priority}
                </span>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Directive Instructions for AI Tutor
            </label>
            <textarea
              rows={3}
              placeholder="e.g., Emphasize conceptual derivations of Carnot efficiency; do not provide direct formulas until the student outlines the temperature cycle."
              value={directiveText}
              onChange={(e) => setDirectiveText(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white p-3 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              data-testid="directive-text-input"
            />
          </div>

          {statusMessage && (
            <div className="rounded-lg bg-sky-50 p-2.5 text-xs text-sky-800 border border-sky-100 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 shrink-0 text-sky-600" />
              <span>{statusMessage}</span>
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting || !directiveText.trim()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-50 transition"
              data-testid="submit-directive-btn"
            >
              <Plus className="h-4 w-4" />
              <span>Publish Directive</span>
            </button>
          </div>
        </form>
      )}

      {/* Active Directives List */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <span>Active Instruction Cascade</span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
            {safeInstructions.length}
          </span>
        </h4>

        {safeInstructions.length === 0 ? (
          <EmptyState
            icon={<Zap className="h-8 w-8 text-slate-400" />}
            title="No Active Directives"
            description="The AI Tutor is operating under standard course syllabus guidance. Add directives above to steer tutor pedagogy."
          />
        ) : (
          <div className="space-y-2.5" data-testid="instructions-list">
            {safeInstructions.map((inst) => (
              <div
                key={inst.id}
                className="flex items-start justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 transition"
                data-testid={`instruction-card-${inst.id}`}
              >
                <div className="space-y-1.5 pr-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider border ${getTierColor(
                        inst.tier
                      )}`}
                    >
                      {inst.tier} TIER
                    </span>
                    <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-700">
                      Priority {inst.priority}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {new Date(inst.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-slate-800 font-normal leading-relaxed">
                    {inst.directive_text}
                  </p>
                </div>

                {onDeactivateInstruction && (
                  <button
                    onClick={() => handleDeactivate(inst.id)}
                    className="text-slate-400 hover:text-rose-600 transition p-1 shrink-0"
                    title="Deactivate Directive"
                    data-testid={`deactivate-btn-${inst.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
