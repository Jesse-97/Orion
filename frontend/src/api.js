import axios from "axios";

// Backend runs on localhost:8000. Synthesis is a local model with a server-side
// timeout up to ~120s, so we allow a generous client timeout (130s).
const client = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 130000,
});

// Normalize FastAPI's {detail} errors (and network errors) into a clean message.
function toError(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return new Error(detail);
  if (Array.isArray(detail) && detail[0]?.msg) return new Error(detail[0].msg);
  if (err?.code === "ECONNABORTED") return new Error("Request timed out. Try again.");
  if (err?.message) return new Error(err.message);
  return new Error("Something went wrong. Is the backend running?");
}

// POST /api/upload — multipart, field name "file".
// Returns { document_id, filename, pages_extracted, chunks_created }.
export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  try {
    const { data } = await client.post("/api/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  } catch (err) {
    throw toError(err);
  }
}

// POST /api/query — JSON { question }.
// Backend returns { query, response: { answer, citation, confidence, reasoning } }.
// We return just the inner response object.
export async function query(question) {
  try {
    const { data } = await client.post("/api/query", { question });
    return data.response;
  } catch (err) {
    throw toError(err);
  }
}
