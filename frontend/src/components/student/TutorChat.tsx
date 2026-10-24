'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Square,
  Sparkles,
  BookOpen,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  RotateCcw,
  Cpu,
} from 'lucide-react';
import { TutorMessage, PedagogyMode, Citation } from '../../lib/types/tutoring';
import { TutorStreamClient } from '../../lib/stream-client';
import { useAuth } from '../../context/AuthContext';

interface TutorChatProps {
  sessionId: string;
  courseTitle?: string;
  initialMessages?: TutorMessage[];
}

export default function TutorChat({
  sessionId,
  courseTitle = 'Course Tutoring',
  initialMessages = [],
}: TutorChatProps) {
  const { token, activeContext } = useAuth();
  const [messages, setMessages] = useState<TutorMessage[]>(
    initialMessages.length > 0
      ? initialMessages
      : [
          {
            id: 'welcome-1',
            sender: 'tutor',
            content: `Hello! I'm your AI Tutor for **${courseTitle}**. Which concept or problem would you like to explore today?`,
            timestamp: new Date().toISOString(),
            status: 'complete',
            mode: 'socratic',
          },
        ]
  );
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<PedagogyMode>('socratic');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  const cancelStreamRef = useRef<(() => void) | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamClientRef = useRef(new TutorStreamClient());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const studentMsg: TutorMessage = {
      id: `msg-${Date.now()}-student`,
      sender: 'student',
      content: trimmed,
      timestamp: new Date().toISOString(),
      mode,
    };

    const pendingTutorMsgId = `msg-${Date.now()}-tutor`;
    const pendingTutorMsg: TutorMessage = {
      id: pendingTutorMsgId,
      sender: 'tutor',
      content: '',
      timestamp: new Date().toISOString(),
      mode,
      status: 'streaming',
      citations: [],
    };

    setMessages((prev) => [...prev, studentMsg, pendingTutorMsg]);
    setInput('');
    setIsStreaming(true);

    const cancelFn = streamClientRef.current.streamTurn(
      sessionId,
      trimmed,
      mode,
      token,
      activeContext.organizationId,
      {
        onToken: (tokenChunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingTutorMsgId ? { ...m, content: m.content + tokenChunk } : m
            )
          );
        },
        onCitation: (citation) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingTutorMsgId
                ? { ...m, citations: [...(m.citations || []), citation] }
                : m
            )
          );
        },
        onComplete: (fullText, citations) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingTutorMsgId
                ? {
                    ...m,
                    content: fullText,
                    citations,
                    status: 'complete',
                    model: 'adaptive-router',
                    provider: 'cloud-gateway',
                  }
                : m
            )
          );
          setIsStreaming(false);
          cancelStreamRef.current = null;
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === pendingTutorMsgId
                ? {
                    ...m,
                    content:
                      m.content ||
                      `Unable to generate response: ${err.message}. Please try again.`,
                    status: 'error',
                  }
                : m
            )
          );
          setIsStreaming(false);
          cancelStreamRef.current = null;
        },
      }
    );

    cancelStreamRef.current = cancelFn;
  };

  const handleCancel = () => {
    if (cancelStreamRef.current) {
      cancelStreamRef.current();
      cancelStreamRef.current = null;
      setIsStreaming(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.status === 'streaming'
            ? { ...m, content: m.content + ' [Cancelled by learner]', status: 'complete' }
            : m
        )
      );
    }
  };

  const handleFeedback = (messageId: string, rating: 'helpful' | 'unhelpful') => {
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, feedback: rating } : m))
    );
  };

  return (
    <div
      className="flex h-[calc(100vh-8rem)] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden"
      data-testid="tutor-chat-container"
    >
      {/* Top Header: Pedagogy mode & Model status */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-slate-50/80 px-6 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-600 text-white shadow-sm">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">{courseTitle}</h2>
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3 text-sky-600" />
                Adaptive Quality Router
              </span>
              <span>•</span>
              <span className="capitalize">{mode.replace('_', ' ')} Mode</span>
            </div>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          {(['socratic', 'explain_first', 'practice_first'] as PedagogyMode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                mode === m
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
              data-testid={`mode-button-${m}`}
            >
              {m === 'socratic'
                ? 'Socratic'
                : m === 'explain_first'
                ? 'Explain First'
                : 'Practice First'}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Stream Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.sender === 'student' ? 'items-end' : 'items-start'
            }`}
            data-testid={`chat-message-${msg.id}`}
          >
            <div
              className={`max-w-2xl rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                msg.sender === 'student'
                  ? 'bg-sky-600 text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm border border-slate-200/60'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {msg.status === 'streaming' && (
                <span className="inline-block w-2 h-4 ml-1 bg-sky-600 animate-pulse align-middle"></span>
              )}
            </div>

            {/* Citations list for Tutor messages */}
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 max-w-2xl">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Sources:
                </span>
                {msg.citations.map((c, i) => (
                  <button
                    key={`${c.chunk_id}-${i}`}
                    onClick={() => setSelectedCitation(c)}
                    className="flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-medium text-slate-600 hover:border-sky-300 hover:text-sky-700 transition"
                    data-testid={`citation-pill-${i}`}
                  >
                    <BookOpen className="h-3 w-3 text-sky-500" />
                    <span>{c.source_title}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Helpfulness feedback for completed Tutor messages */}
            {msg.sender === 'tutor' && msg.status === 'complete' && (
              <div className="mt-1.5 flex items-center gap-2 text-[11px] text-slate-400">
                <span>Was this helpful?</span>
                <button
                  onClick={() => handleFeedback(msg.id, 'helpful')}
                  className={`rounded p-1 hover:text-emerald-600 transition ${
                    msg.feedback === 'helpful' ? 'text-emerald-600 font-bold' : ''
                  }`}
                  data-testid="feedback-helpful"
                  title="Helpful"
                >
                  <ThumbsUp className="h-3 w-3" />
                </button>
                <button
                  onClick={() => handleFeedback(msg.id, 'unhelpful')}
                  className={`rounded p-1 hover:text-rose-600 transition ${
                    msg.feedback === 'unhelpful' ? 'text-rose-600 font-bold' : ''
                  }`}
                  data-testid="feedback-unhelpful"
                  title="Not helpful"
                >
                  <ThumbsDown className="h-3 w-3" />
                </button>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Selected Citation Drawer/Modal */}
      {selectedCitation && (
        <div
          className="border-t border-slate-200 bg-amber-50/70 p-4 text-xs"
          data-testid="citation-preview-panel"
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-semibold text-amber-900 flex items-center gap-1.5">
              <BookOpen className="h-3.5 w-3.5 text-amber-700" />
              Source Reference: {selectedCitation.source_title}
            </span>
            <button
              onClick={() => setSelectedCitation(null)}
              className="text-amber-800 hover:text-amber-950 font-bold"
            >
              ✕
            </button>
          </div>
          <p className="text-amber-800 font-mono text-[11px] bg-white/70 p-2.5 rounded-lg border border-amber-200 leading-normal">
            &ldquo;{selectedCitation.snippet}&rdquo;
          </p>
        </div>
      )}

      {/* Input bar */}
      <div className="border-t border-slate-200 bg-white p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or explain your reasoning..."
            disabled={isStreaming}
            className="flex-1 rounded-xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-800 focus:border-sky-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-sky-500 disabled:opacity-50"
            data-testid="tutor-chat-input"
          />

          {isStreaming ? (
            <button
              type="button"
              onClick={handleCancel}
              className="flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-3 text-xs font-semibold text-white hover:bg-rose-700 transition"
              data-testid="tutor-chat-stop-button"
            >
              <Square className="h-4 w-4" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="flex items-center gap-1.5 rounded-xl bg-sky-600 px-5 py-3 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-40 transition"
              data-testid="tutor-chat-send-button"
            >
              <Send className="h-4 w-4" />
              <span>Send</span>
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
