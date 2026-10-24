'use client';

import React, { useState } from 'react';
import { AdminAiPolicy } from '../../lib/types/admin';
import { Cpu, Key, ShieldCheck, CheckCircle2, Save, Sparkles } from 'lucide-react';

interface AiPolicyManagerProps {
  policy: AdminAiPolicy;
  onSavePolicy: (allowedModels: string[], routingStrategy: string) => Promise<void>;
}

const SUPPORTED_MODELS = [
  { id: 'gpt-4o', label: 'OpenAI GPT-4o', provider: 'openai', desc: 'Highest reasoning and multi-modal pedagogical performance' },
  { id: 'gpt-4o-mini', label: 'OpenAI GPT-4o-mini', provider: 'openai', desc: 'Fast, cost-efficient tutoring execution' },
  { id: 'claude-3-5-sonnet-20241022', label: 'Anthropic Claude 3.5 Sonnet', provider: 'anthropic', desc: 'Superior nuanced explanation and code synthesis' },
  { id: 'claude-3-haiku', label: 'Anthropic Claude 3 Haiku', provider: 'anthropic', desc: 'Ultra-low latency conversational tutor' },
  { id: 'gemini-1.5-pro', label: 'Google Gemini 1.5 Pro', provider: 'gemini', desc: 'Massive context window for full textbook grounding' },
  { id: 'gemini-1.5-flash', label: 'Google Gemini 1.5 Flash', provider: 'gemini', desc: 'High-speed diagnostic evaluations' },
  { id: 'llama-3.1-70b', label: 'Meta Llama 3.1 70B', provider: 'openrouter', desc: 'Open-weights capable model via OpenRouter' },
];

const ROUTING_STRATEGIES = [
  { id: 'quality_first', label: 'Quality First', desc: 'Prioritizes highest benchmark scores and mastery pedagogical efficacy' },
  { id: 'cost_efficient', label: 'Cost Efficient', desc: 'Balances quality while minimizing per-token expenditure' },
  { id: 'latency_optimized', label: 'Latency Optimized', desc: 'Directs real-time tutoring turns to the fastest available endpoints' },
];

export default function AiPolicyManager({ policy, onSavePolicy }: AiPolicyManagerProps) {
  const [selectedModels, setSelectedModels] = useState<string[]>(
    policy.allowed_models.includes('*')
      ? SUPPORTED_MODELS.map((m) => m.id)
      : policy.allowed_models
  );
  const [strategy, setStrategy] = useState<string>(policy.routing_strategy || 'quality_first');
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const toggleModel = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      if (selectedModels.length === 1) return; // Maintain at least one model
      setSelectedModels(selectedModels.filter((id) => id !== modelId));
    } else {
      setSelectedModels([...selectedModels, modelId]);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setStatusMessage(null);
      await onSavePolicy(selectedModels, strategy);
      setStatusMessage('AI Routing Policy updated successfully.');
    } catch {
      setStatusMessage('Failed to update AI policy.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="ai-policy-manager">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-purple-600" />
            <h3 className="text-base font-bold text-slate-900">
              AI Routing Policy & Model Whitelist
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Control allowed inference models, adaptive routing strategy, and view credential health.
          </p>
        </div>
        <button
          type="button"
          disabled={saving}
          onClick={handleSave}
          className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-700 disabled:opacity-50"
          data-testid="btn-save-ai-policy"
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save Policy'}
        </button>
      </div>

      {statusMessage && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-3 text-sm font-medium text-emerald-800 border border-emerald-200" data-testid="ai-policy-status">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Routing Strategy Selector */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-purple-600" />
          Active Routing Strategy
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {ROUTING_STRATEGIES.map((strat) => (
            <label
              key={strat.id}
              className={`cursor-pointer rounded-xl border p-4 transition ${
                strategy === strat.id
                  ? 'border-purple-600 bg-purple-50/50 ring-2 ring-purple-600/20'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
              data-testid={`strategy-option-${strat.id}`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900 text-sm">{strat.label}</span>
                <input
                  type="radio"
                  name="routing_strategy"
                  value={strat.id}
                  checked={strategy === strat.id}
                  onChange={() => setStrategy(strat.id)}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500"
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">{strat.desc}</p>
            </label>
          ))}
        </div>
      </div>

      {/* Allowed Models Whitelist */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          Allowed Models Whitelist
        </h4>
        <div className="space-y-3">
          {SUPPORTED_MODELS.map((model) => {
            const isChecked = selectedModels.includes(model.id);
            return (
              <label
                key={model.id}
                className={`flex items-center justify-between rounded-xl border p-3.5 transition cursor-pointer ${
                  isChecked
                    ? 'border-purple-200 bg-purple-50/30'
                    : 'border-slate-100 hover:border-slate-200 opacity-70'
                }`}
                data-testid={`model-whitelist-${model.id}`}
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleModel(model.id)}
                    className="h-4 w-4 rounded text-purple-600 focus:ring-purple-500"
                  />
                  <div>
                    <span className="font-semibold text-sm text-slate-900">{model.label}</span>
                    <span className="ml-2 inline-flex items-center rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                      {model.id}
                    </span>
                    <p className="text-xs text-slate-500 mt-0.5">{model.desc}</p>
                  </div>
                </div>
                <span className="text-xs font-semibold text-slate-400 uppercase">
                  {model.provider}
                </span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Configured Provider Credentials (Masked) */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h4 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
          <Key className="h-4 w-4 text-amber-600" />
          Configured Provider Connections
        </h4>
        {policy.configured_providers && policy.configured_providers.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {policy.configured_providers.map((cp) => (
              <div
                key={cp.id}
                className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                data-testid={`provider-connection-${cp.id}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs uppercase text-slate-700">{cp.provider}</span>
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800">
                    Active
                  </span>
                </div>
                <p className="mt-2 font-mono text-xs text-slate-600">{cp.key_masked}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400">
            No organization BYOK keys active. System will utilize default platform fallback models.
          </p>
        )}
      </div>
    </div>
  );
}
