'use client';

import React, { useState } from 'react';
import { InterventionItem } from '../../lib/types/teacher';
import EmptyState from '../common/EmptyState';
import { AlertCircle, CheckCircle, ShieldAlert, MessageSquare } from 'lucide-react';

interface InterventionQueueProps {
  interventions: InterventionItem[];
  onAcknowledge?: (interventionId: string, notes?: string, resolve?: boolean) => Promise<void>;
}

export default function InterventionQueue({
  interventions,
  onAcknowledge,
}: InterventionQueueProps) {
  const safeInterventions = Array.isArray(interventions) ? interventions : [];
  const [selectedIntervention, setSelectedIntervention] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'HIGH':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'LOW':
        return 'bg-sky-100 text-sky-800 border-sky-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  const handleAction = async (id: string, resolve: boolean) => {
    if (!onAcknowledge) return;
    try {
      setIsSubmitting(true);
      await onAcknowledge(id, notes.trim() || undefined, resolve);
      setSelectedIntervention(null);
      setNotes('');
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-4" data-testid="intervention-queue">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-rose-600" />
          <h3 className="text-base font-semibold text-slate-900">
            Learner Intervention Queue
          </h3>
        </div>
        <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700 border border-rose-200">
          {safeInterventions.length} Pending
        </span>
      </div>

      {safeInterventions.length === 0 ? (
        <EmptyState
          icon={<CheckCircle className="h-8 w-8 text-emerald-500" />}
          title="All Clear!"
          description="No students currently meet the intervention threshold for learning distress or persistent misconceptions."
        />
      ) : (
        <div className="space-y-3" data-testid="interventions-list">
          {safeInterventions.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-slate-300 transition space-y-3"
              data-testid={`intervention-card-${item.id}`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-bold border ${getSeverityBadge(
                      item.severity
                    )}`}
                    data-testid={`severity-badge-${item.id}`}
                  >
                    {item.severity}
                  </span>
                  <span className="font-semibold text-sm text-slate-900">
                    {item.student_name}
                  </span>
                  {item.concept_id && (
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                      {item.concept_id}
                    </span>
                  )}
                </div>
                <span className="text-xs text-slate-400">
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>

              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                {item.reason}
              </p>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] font-medium text-slate-400">
                  Status: <strong className="text-slate-600">{item.status}</strong>
                </span>

                <div className="flex items-center gap-2">
                  {selectedIntervention === item.id ? (
                    <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2">
                      <input
                        type="text"
                        placeholder="Resolution or coaching notes..."
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs focus:border-sky-500 focus:outline-none"
                        data-testid="intervention-notes-input"
                      />
                      <div className="flex gap-1.5">
                        <button
                          onClick={() => handleAction(item.id, false)}
                          disabled={isSubmitting}
                          className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-200 disabled:opacity-50"
                          data-testid="ack-btn"
                        >
                          Acknowledge
                        </button>
                        <button
                          onClick={() => handleAction(item.id, true)}
                          disabled={isSubmitting}
                          className="rounded-md bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                          data-testid="resolve-btn"
                        >
                          Resolve
                        </button>
                        <button
                          onClick={() => setSelectedIntervention(null)}
                          className="rounded-md px-2 py-1 text-xs text-slate-400 hover:text-slate-600"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setSelectedIntervention(item.id)}
                      className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition shadow-sm"
                      data-testid={`open-action-btn-${item.id}`}
                    >
                      <MessageSquare className="h-3.5 w-3.5 text-slate-500" />
                      <span>Take Action</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
