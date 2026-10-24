import React from 'react';

export default function LoadingSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4 animate-pulse w-full" data-testid="loading-skeleton">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="h-4 bg-slate-200 rounded w-1/3 mb-3"></div>
          <div className="h-3 bg-slate-100 rounded w-3/4 mb-2"></div>
          <div className="h-3 bg-slate-100 rounded w-1/2"></div>
        </div>
      ))}
    </div>
  );
}
