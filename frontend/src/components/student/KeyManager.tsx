'use client';

import React, { useState } from 'react';
import { Key, ShieldCheck, Trash2, Plus, AlertCircle, EyeOff } from 'lucide-react';
import { ProviderConnection, ProviderType } from '../../lib/types/ai';
import { api } from '../../lib/api-client';

interface KeyManagerProps {
  initialConnections: ProviderConnection[];
}

export default function KeyManager({ initialConnections }: KeyManagerProps) {
  const [connections, setConnections] = useState<ProviderConnection[]>(initialConnections);
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>('openai');
  const [label, setLabel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const newConn = await api.addProviderConnection({
        provider: selectedProvider,
        label: label.trim() || `${selectedProvider.toUpperCase()} Key`,
        api_key: apiKey.trim(),
        scope: 'PERSONAL',
      });

      setConnections((prev) => [...prev, newConn]);
      setApiKey('');
      setLabel('');
      setShowAddForm(false);
    } catch (err: unknown) {
      setError((err as Error).message || 'Failed to save provider connection');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (connectionId: string) => {
    if (!window.confirm('Are you sure you want to revoke and delete this API credential?')) {
      return;
    }

    try {
      await api.deleteProviderConnection(connectionId);
      setConnections((prev) => prev.filter((c) => c.id !== connectionId));
    } catch (err: unknown) {
      alert((err as Error).message || 'Failed to revoke connection');
    }
  };

  return (
    <div className="space-y-6" data-testid="key-manager-container">
      {/* Informational Banner */}
      <div className="rounded-2xl border border-sky-100 bg-sky-50/60 p-6">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-sky-600 mt-0.5 shrink-0" />
          <div className="text-xs text-sky-950 space-y-1">
            <h4 className="font-bold text-sm text-sky-900">
              Bring Your Own Key (BYOK) Security Vault
            </h4>
            <p className="leading-relaxed text-sky-800">
              Your API credentials are encrypted with server-side AES-256-GCM. Gayatri Cloud never
              exposes or returns raw secret keys to your browser after they are saved.
            </p>
          </div>
        </div>
      </div>

      {/* Connection List */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Key className="h-4 w-4 text-sky-600" />
            <span>Active Provider Connections</span>
          </h3>

          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-1.5 rounded-lg bg-sky-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-sky-700 transition"
            data-testid="toggle-add-key-button"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Connection</span>
          </button>
        </div>

        {/* Add Connection Form Drawer */}
        {showAddForm && (
          <form
            onSubmit={handleAdd}
            className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-5 text-xs space-y-4"
            data-testid="add-key-form"
          >
            <div className="font-semibold text-slate-800 text-sm">Add AI Provider Credential</div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block font-medium text-slate-700 mb-1">AI Provider</label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value as ProviderType)}
                  className="w-full rounded-lg border border-slate-300 bg-white p-2.5 text-slate-800 focus:border-sky-500 focus:outline-none"
                  data-testid="provider-select"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Connection Label</label>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="e.g. My Personal OpenAI Key"
                  className="w-full rounded-lg border border-slate-300 bg-white p-2.5 text-slate-800 focus:border-sky-500 focus:outline-none"
                  data-testid="label-input"
                />
              </div>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">API Key Secret</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Paste your API key (e.g. sk-...)"
                required
                className="w-full rounded-lg border border-slate-300 bg-white p-2.5 font-mono text-xs text-slate-800 focus:border-sky-500 focus:outline-none"
                data-testid="api-key-input"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Saved into encrypted vault. Never displayed again.
              </span>
            </div>

            {error && (
              <div className="rounded-lg bg-rose-50 border border-rose-200 p-2.5 text-rose-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="rounded-lg border border-slate-300 bg-white px-3.5 py-1.5 font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !apiKey.trim()}
                className="rounded-lg bg-sky-600 px-4 py-1.5 font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
                data-testid="save-key-button"
              >
                {isSubmitting ? 'Encrypting & Saving...' : 'Save Connection'}
              </button>
            </div>
          </form>
        )}

        {/* Existing Connections Table */}
        {connections.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No personal AI provider keys configured. The platform default router will be used.
          </div>
        ) : (
          <div className="space-y-3">
            {connections.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-xl border border-slate-200 p-4 text-xs"
                data-testid={`connection-row-${c.id}`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900">{c.label}</span>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-mono uppercase text-slate-700">
                      {c.provider}
                    </span>
                    <span className="rounded bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-sky-800">
                      {c.scope}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500 font-mono text-[11px] mt-1">
                    <EyeOff className="h-3 w-3 text-slate-400" />
                    <span>{c.masked_key}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                    Active
                  </span>
                  <button
                    onClick={() => handleDelete(c.id)}
                    className="rounded p-1.5 text-slate-400 hover:text-rose-600 transition"
                    title="Revoke and delete key"
                    data-testid={`delete-key-${c.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
