import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { query } from "../api";
import CitationBlock from "./CitationBlock";
import ConfidenceBadge from "./ConfidenceBadge";

function LoadingSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <div className="flex items-center gap-3 text-sm text-zinc-400">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-600 border-t-accent" />
        Analyzing documents…
      </div>
      <div className="mt-5 space-y-3">
        {[100, 92, 78].map((w) => (
          <div
            key={w}
            className="relative h-4 overflow-hidden rounded bg-zinc-800"
            style={{ width: `${w}%` }}
          >
            <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-zinc-700/60 to-transparent" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function QueryView() {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | result | error
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [showReasoning, setShowReasoning] = useState(false);

  async function submit() {
    const q = question.trim();
    if (!q || status === "loading") return;
    setStatus("loading");
    setError("");
    setResponse(null);
    setShowReasoning(false);
    try {
      const res = await query(q);
      setResponse(res);
      setStatus("result");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <h2 className="text-lg font-semibold text-zinc-100">Ask a question</h2>
      <p className="mt-1 text-sm text-zinc-400">
        Query your indexed documents. Answers are grounded in retrieved passages and
        cited.
      </p>

      <div className="mt-6">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={onKeyDown}
          rows={3}
          placeholder="e.g. What is the termination notice period?"
          className="w-full resize-none rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent"
        />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-zinc-500">
            Enter to ask · Shift+Enter for a new line
          </span>
          <button
            onClick={submit}
            disabled={status === "loading" || !question.trim()}
            className="rounded-lg bg-accent-deep px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-40"
          >
            {status === "loading" ? "Analyzing…" : "Ask"}
          </button>
        </div>
      </div>

      <div className="mt-6">
        <AnimatePresence mode="wait">
          {status === "loading" && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <LoadingSkeleton />
            </motion.div>
          )}

          {status === "error" && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-lg border border-rose-500/30 bg-rose-500/5 px-4 py-3 text-sm text-rose-400"
            >
              {error}
            </motion.div>
          )}

          {status === "result" && response && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-[0_0_0_1px_rgba(34,211,238,0.06)]"
            >
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Answer
                </span>
                <ConfidenceBadge confidence={response.confidence} />
              </div>

              <p className="text-xl leading-relaxed text-zinc-50">
                {response.answer}
              </p>

              <CitationBlock citation={response.citation} />

              {response.reasoning && (
                <div className="mt-5 border-t border-zinc-800 pt-4">
                  <button
                    onClick={() => setShowReasoning((s) => !s)}
                    className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 transition-colors hover:text-accent"
                  >
                    <svg
                      className={`h-3.5 w-3.5 transition-transform ${
                        showReasoning ? "rotate-90" : ""
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M8.25 4.5l7.5 7.5-7.5 7.5"
                      />
                    </svg>
                    Reasoning
                  </button>
                  <AnimatePresence initial={false}>
                    {showReasoning && (
                      <motion.p
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden text-sm leading-relaxed text-zinc-400"
                      >
                        <span className="mt-2 block">{response.reasoning}</span>
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
