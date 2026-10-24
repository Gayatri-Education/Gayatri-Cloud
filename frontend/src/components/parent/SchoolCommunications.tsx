'use client';

import React from 'react';
import { ChildCommunicationItem } from '../../lib/types/parent';
import EmptyState from '../common/EmptyState';
import { MessageSquare, Bell, Calendar, User } from 'lucide-react';

interface SchoolCommunicationsProps {
  communications: ChildCommunicationItem[];
}

export default function SchoolCommunications({ communications }: SchoolCommunicationsProps) {
  const safeComms = Array.isArray(communications) ? communications : [];

  return (
    <div className="space-y-4" data-testid="school-communications">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-sky-600" />
          <h3 className="text-base font-bold text-slate-900">
            Class Notices & Teacher Updates
          </h3>
        </div>
        <span className="text-xs text-slate-400">
          {safeComms.length} {safeComms.length === 1 ? 'notice' : 'notices'} posted
        </span>
      </div>

      {safeComms.length === 0 ? (
        <EmptyState
          icon={<MessageSquare className="h-8 w-8 text-slate-400" />}
          title="No School Notices"
          description="There are currently no active course announcements for this learner."
        />
      ) : (
        <div className="space-y-3" data-testid="communications-list">
          {safeComms.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:border-slate-300 transition space-y-2"
              data-testid={`communication-card-${item.id}`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <h4 className="text-sm font-bold text-slate-900">{item.title}</h4>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Calendar className="h-3.5 w-3.5" />
                  <span>{new Date(item.posted_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-sky-700 font-medium">
                <User className="h-3.5 w-3.5" />
                <span>Posted by {item.teacher_name}</span>
              </div>

              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                {item.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
