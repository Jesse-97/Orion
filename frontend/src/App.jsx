import { useState } from "react";
import { motion } from "framer-motion";
import UploadView from "./components/UploadView";
import QueryView from "./components/QueryView";

const TABS = [
  { id: "query", label: "Query" },
  { id: "upload", label: "Upload" },
];

export default function App() {
  const [tab, setTab] = useState("query");

  return (
    <div className="min-h-full bg-zinc-950">
      <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-accent shadow-[0_0_12px_2px_rgba(34,211,238,0.5)]" />
            <span className="text-base font-semibold tracking-tight text-zinc-50">
              Lex<span className="text-accent">RAG</span>
            </span>
            <span className="ml-2 hidden text-xs text-zinc-500 sm:inline">
              Your legal assistant
            </span>
          </div>

          <nav className="flex items-center gap-1 rounded-lg bg-zinc-900 p-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`relative rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  tab === t.id ? "text-zinc-50" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {tab === t.id && (
                  <motion.span
                    layoutId="tab-pill"
                    className="absolute inset-0 rounded-md bg-zinc-800"
                    transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  />
                )}
                <span className="relative">{t.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-10">
        {tab === "query" ? <QueryView /> : <UploadView />}
      </main>
    </div>
  );
}
