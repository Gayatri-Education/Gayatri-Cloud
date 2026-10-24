'use client';

import React from 'react';
import { LinkedChild } from '../../lib/types/parent';
import { User, CheckCircle, Clock, Plus } from 'lucide-react';
import Link from 'next/link';

interface ChildSelectorProps {
  childrenList: LinkedChild[];
  selectedStudentId: string | null;
  onSelectChild: (studentId: string) => void;
}

export default function ChildSelector({
  childrenList,
  selectedStudentId,
  onSelectChild,
}: ChildSelectorProps) {
  const safeList = Array.isArray(childrenList) ? childrenList : [];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 rounded-2xl border border-slate-200 bg-white shadow-sm" data-testid="child-selector">
      <div className="flex items-center gap-2">
        <User className="h-5 w-5 text-sky-600" />
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Linked Learner:
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {safeList.map((child) => {
          const isSelected = selectedStudentId === child.student_id;
          const isVerified = child.verification_status === 'verified';

          return (
            <button
              key={child.student_id}
              onClick={() => onSelectChild(child.student_id)}
              disabled={!isVerified}
              className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-medium transition ${
                isSelected
                  ? 'bg-sky-600 text-white shadow-xs'
                  : isVerified
                  ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  : 'bg-slate-50 text-slate-400 cursor-not-allowed opacity-75'
              }`}
              data-testid={`child-pill-${child.student_id}`}
            >
              <span className="font-semibold">{child.student_name}</span>
              {isVerified ? (
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    isSelected ? 'bg-sky-500 text-white' : 'bg-slate-200 text-slate-700'
                  }`}
                >
                  {Math.round(child.average_mastery * 100)}%
                </span>
              ) : (
                <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-600 font-semibold">
                  <Clock className="h-3 w-3" />
                  Pending
                </span>
              )}
            </button>
          );
        })}

        <Link
          href="/parent/children"
          className="inline-flex items-center gap-1 rounded-xl border border-dashed border-slate-300 px-3 py-2 text-xs font-semibold text-slate-600 hover:border-sky-400 hover:text-sky-600 transition"
          data-testid="link-child-link"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Link Child</span>
        </Link>
      </div>
    </div>
  );
}
