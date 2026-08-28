import React, { useState } from 'react';
import { Brain, Loader2, Sparkles, AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react';

interface EvidenceSources {
  used: string[];
  unavailable: string[];
}

interface InvestigationResponse {
  event_id: string;
  question: string;
  answer: string;
  evidence_sources: EvidenceSources;
  latency_ms: number;
}

interface AskInvestigationAIProps {
  eventId: string;
}

export const AskInvestigationAI: React.FC<AskInvestigationAIProps> = ({ eventId }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InvestigationResponse | null>(null);
  const [customQuestion, setCustomQuestion] = useState('');

  const suggestedQuestions = [
    "Why is this event high priority?",
    "What evidence supports it?",
    "What is unusual compared with historical behavior?",
    "What evidence is missing?",
    "Is this a confirmed fire?"
  ];

  const handleAsk = async (question: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/agent/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, question })
      });

      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }

      const data: InvestigationResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to communicate with AI Agent.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3.5 flex flex-col gap-3.5 mt-2">
      {/* Title */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <Brain className="w-4 h-4 text-purple-400 animate-pulse" />
        <h3 className="font-extrabold text-slate-200 text-xs tracking-wider uppercase flex items-center gap-1.5">
          Ask Anomaly AI
          <Sparkles className="w-3 h-3 text-amber-400" />
        </h3>
      </div>

      {/* Suggested Questions Buttons */}
      <div className="flex flex-col gap-1.5">
        <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider mb-0.5">Suggested Inquiries</span>
        <div className="flex flex-wrap gap-1.5">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              disabled={loading}
              onClick={() => handleAsk(q)}
              className="text-[10px] text-left px-2.5 py-1.5 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-850 hover:text-white transition-all disabled:opacity-50 select-none font-sans"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Inquiry Box */}
      <div className="flex gap-1.5 border-t border-slate-900 pt-2.5">
        <input
          type="text"
          value={customQuestion}
          disabled={loading}
          onChange={(e) => setCustomQuestion(e.target.value)}
          placeholder="Ask a custom question..."
          className="flex-1 text-[10px] bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-purple-500 font-sans"
        />
        <button
          disabled={loading || !customQuestion.trim()}
          onClick={() => {
            handleAsk(customQuestion);
            setCustomQuestion('');
          }}
          className="bg-purple-600/85 hover:bg-purple-600 text-white rounded px-2.5 py-1 text-[10px] font-bold transition-all disabled:opacity-50 disabled:hover:bg-purple-600/85 select-none"
        >
          Ask
        </button>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-6 bg-slate-900/40 rounded border border-dashed border-slate-800">
          <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest animate-pulse">
            Consulting Satellite Intelligence...
          </span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-2 p-2 bg-red-950/40 border border-red-900/60 rounded text-red-300 text-[10.5px] leading-relaxed">
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 text-red-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* AI Response Card */}
      {result && !loading && (
        <div className="flex flex-col gap-3 bg-slate-900/80 border border-slate-800 rounded p-3">
          {/* Answer Area */}
          <div className="text-[11px] leading-relaxed text-slate-200 font-sans whitespace-pre-wrap select-text border-b border-slate-800/60 pb-3">
            {result.answer}
          </div>

          {/* Audit Sources Panel */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">
              Evidence Audit (Latency: {result.latency_ms}ms)
            </span>
            <div className="flex flex-col gap-1.5">
              {/* Used checklist */}
              {result.evidence_sources.used.map((source, idx) => (
                <div key={idx} className="flex items-center gap-2 text-[10px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                  <span className="font-semibold text-slate-350">Used: {source}</span>
                </div>
              ))}

              {/* Unavailable checklist */}
              {result.evidence_sources.unavailable.map((source, idx) => (
                <div key={idx} className="flex items-center gap-2 text-[10px] text-slate-500">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-650 flex-shrink-0" />
                  <span className="font-semibold line-through">Unavailable: {source}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
