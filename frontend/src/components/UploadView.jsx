import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { uploadDocument } from "../api";

const ACCEPTED = ["pdf", "docx"];

function isAccepted(file) {
  const ext = file.name.split(".").pop()?.toLowerCase();
  return ACCEPTED.includes(ext);
}

export default function UploadView() {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");

  async function handleFile(file) {
    if (!file) return;
    if (!isAccepted(file)) {
      setStatus("error");
      setError("Only PDF and DOCX files are supported.");
      return;
    }
    setFileName(file.name);
    setStatus("uploading");
    setError("");
    setResult(null);
    try {
      const data = await uploadDocument(file);
      setResult(data);
      setStatus("success");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <h2 className="text-lg font-semibold text-zinc-100">Upload a document</h2>
      <p className="mt-1 text-sm text-zinc-400">
        Add a PDF or DOCX to the knowledge base. It will be chunked, embedded and
        indexed for querying.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`mt-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
          dragging
            ? "border-accent bg-cyan-500/5"
            : "border-zinc-700 hover:border-zinc-600 bg-zinc-900/40"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <svg
          className="mb-3 h-10 w-10 text-zinc-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 7.5 7.5 12M12 7.5V21"
          />
        </svg>
        <p className="text-sm text-zinc-300">
          <span className="font-medium text-accent">Click to browse</span> or drag
          &amp; drop
        </p>
        <p className="mt-1 text-xs text-zinc-500">PDF or DOCX</p>
      </div>

      <div className="mt-5">
        <AnimatePresence mode="wait">
          {status === "uploading" && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 text-sm text-zinc-300"
            >
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-600 border-t-accent" />
              Ingesting <span className="font-medium text-zinc-100">{fileName}</span>…
            </motion.div>
          )}

          {status === "success" && result && (
            <motion.div
              key="success"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 px-4 py-4"
            >
              <p className="text-sm font-medium text-emerald-400">
                Uploaded successfully
              </p>
              <p className="mt-1 text-sm text-zinc-300">{result.filename}</p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <span className="rounded-md bg-zinc-800 px-2.5 py-1 text-zinc-300">
                  {result.pages_extracted} pages extracted
                </span>
                <span className="rounded-md bg-zinc-800 px-2.5 py-1 text-zinc-300">
                  {result.chunks_created} chunks created
                </span>
              </div>
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
        </AnimatePresence>
      </div>
    </div>
  );
}
