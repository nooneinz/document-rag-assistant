async function json(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const listDocuments = () => fetch("/api/documents").then(json);

export const uploadDocument = (file) => {
  const form = new FormData();
  form.append("file", file);
  return fetch("/api/documents", { method: "POST", body: form }).then(json);
};

export const deleteDocument = (id) => fetch(`/api/documents/${id}`, { method: "DELETE" }).then(json);

export const askQuestion = (question, docIds) =>
  fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_ids: docIds?.length ? docIds : null }),
  }).then(json);

export const fileUrl = (id) => `/api/documents/${id}/file`;
