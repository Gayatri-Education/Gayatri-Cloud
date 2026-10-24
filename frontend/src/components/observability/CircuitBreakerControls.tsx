'use client';

import React, { useState } from 'react';
import { api } from '../../lib/api-client';
import { CircuitBreakerItem } from '../../lib/types/observability';
import { Zap, ZapOff, RotateCcw, AlertOctagon } from 'lucide-react';

interface Props {
  breakers: CircuitBreakerItem[];
  onRefresh: () => void;
}

export default function CircuitBreakerControls({ breakers, onRefresh }: Props) {
  const [loadingProvider, setLoadingProvider] = useState<string | null>(null);

  const handleTrip = async (provider: string) => {
    const reason = window.prompt(
      `Enter emergency reason for tripping breaker '${provider}':`,
      'Manual administrative override'
    );
    if (!reason) return;

    try {
      setLoadingProvider(provider);
      await api.tripCircuitBreaker(provider, reason);
      onRefresh();
    } catch {
      // error
    } finally {
      setLoadingProvider(null);
    }
  };

  const handleReset = async (provider: string) => {
    try {
      setLoadingProvider(provider);
      await api.resetCircuitBreaker(provider);
      onRefresh();
    } catch {
      // error
    } finally {
      setLoadingProvider(null);
    }
  };

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4"
      data-testid="circuit-breaker-controls"
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <AlertOctagon className="h-5 w-5 text-amber-600" />
            <span>AI Provider Circuit Breakers & Emergency Kill-Switches</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            State machines automatically fast-fail failing AI providers. Administrators can manually trip or restore circuits.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {breakers.map((b) => {
          const isOpen = b.state === 'OPEN';
          const isHalfOpen = b.state === 'HALF_OPEN';
          const isLoading = loadingProvider === b.name;

          return (
            <div
              key={b.name}
              className={`rounded-xl border p-4 transition ${
                isOpen
                  ? 'border-rose-300 bg-rose-50/50'
                  : isHalfOpen
                  ? 'border-amber-300 bg-amber-50/50'
                  : 'border-slate-200 bg-slate-50/40'
              }`}
              data-testid={`breaker-card-${b.name}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs uppercase tracking-wide text-slate-900">
                  {b.name}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    isOpen
                      ? 'bg-rose-100 text-rose-800'
                      : isHalfOpen
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                  data-testid={`breaker-state-${b.name}`}
                >
                  {b.state}
                </span>
              </div>

              <div className="mt-2 text-[11px] text-slate-500 space-y-0.5">
                <div>Failures: {b.consecutive_failures}</div>
                {b.is_manual_trip && (
                  <div className="text-rose-600 font-semibold truncate">
                    Tripped: {b.manual_trip_reason || 'Manual'}
                  </div>
                )}
              </div>

              <div className="mt-3 flex items-center gap-2 pt-2 border-t border-slate-200/60">
                {isOpen ? (
                  <button
                    onClick={() => handleReset(b.name)}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
                    data-testid={`reset-btn-${b.name}`}
                  >
                    <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
                    <span>Reset Circuit</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleTrip(b.name)}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-1.5 rounded-lg border border-rose-200 bg-rose-100/70 px-2.5 py-1 text-xs font-semibold text-rose-800 hover:bg-rose-200 disabled:opacity-50 transition"
                    data-testid={`kill-switch-btn-${b.name}`}
                  >
                    <ZapOff className="h-3.5 w-3.5 text-rose-600" />
                    <span>Emergency Trip</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
