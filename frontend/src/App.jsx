import { useEffect, useRef, useState } from "react";
import { askQuestion, deleteDocument, fileUrl, listDocuments, uploadDocument } from "./api.js";
import { STRINGS } from "./i18n.js";

export default function App() {
  const [lang, setLang] = useState("en");
  const t = STRINGS[lang];
  const [docs, setDocs] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null); // {doc_id, page}
  const endRef = useRef(null);

  const refresh = () => listDocuments().then(setDocs).catch((e) => setError(e.message));
  useEffect(() => { refresh(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);

  async function onUpload(e) {
    const files = [...e.target.files];
    e.target.value = "";
    setUploading(true);
    setError("");
    try {
      for (const f of files) {
        const d = await uploadDocument(f);
        setPreview({ doc_id: d.doc_id, page: 1 });
      }
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function onDelete(id) {
    await deleteDocument(id);
    if (preview?.doc_id === id) setPreview(null);
    refresh();
  }

  async function onSend(e) {
    e.preventDefault();
    const q = input.trim();
    if (!q || busy) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const r = await askQuestion(q);
      setMessages((m) => [...m, { role: "bot", ...r }]);
      if (r.sources[0]) setPreview({ doc_id: r.sources[0].doc_id, page: r.sources[0].page });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app" dir={lang === "ar" ? "rtl" : "ltr"}>
      <header>
        <h1>{t.title}</h1>
        <button className="ghost" onClick={() => setLang(lang === "en" ? "ar" : "en")}>
          {lang === "en" ? "العربية" : "English"}
        </button>
      </header>

      <main>
        <section className="viewer">
          <div className="docbar">
            <strong>{t.docs}</strong>
            <label className="btn">
              {uploading ? t.uploading : t.upload}
              <input type="file" accept="application/pdf" multiple hidden onChange={onUpload} disabled={uploading} />
            </label>
          </div>
          <ul className="doclist">
            {docs.length === 0 && <li className="muted">{t.noDocs}</li>}
            {docs.map((d) => (
              <li key={d.doc_id} className={preview?.doc_id === d.doc_id ? "active" : ""}>
                <button className="link" onClick={() => setPreview({ doc_id: d.doc_id, page: 1 })}>{d.filename}</button>
                <button className="ghost small" onClick={() => onDelete(d.doc_id)}>{t.delete}</button>
              </li>
            ))}
          </ul>
          <div className="pdf">
            {preview ? (
              <iframe
                key={`${preview.doc_id}-${preview.page}`}
                title="pdf"
                src={`${fileUrl(preview.doc_id)}#page=${preview.page}`}
              />
            ) : (
              <p className="muted center">{t.selectDoc}</p>
            )}
          </div>
        </section>

        <section className="chat">
          <div className="messages">
            {messages.length === 0 && <p className="muted center">{t.welcome}</p>}
            {messages.map((m, i) =>
              m.role === "user" ? (
                <div key={i} className="msg user">{m.text}</div>
              ) : (
                <div key={i} className={`msg bot ${m.sufficient ? "" : "warn"}`}>
                  {!m.sufficient && <span className="badge">{t.insufficient}</span>}
                  <p>{m.answer}</p>
                  {m.sources.length > 0 && (
                    <div className="sources">
                      <small>{t.sources}</small>
                      {m.sources.map((s) => (
                        <button
                          key={s.id}
                          className="source"
                          title={s.text}
                          onClick={() => setPreview({ doc_id: s.doc_id, page: s.page })}
                        >
                          [{s.id}] {s.filename} · {t.page} {s.page}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
            {busy && <div className="msg bot muted">{t.thinking}</div>}
            <div ref={endRef} />
          </div>
          {error && <div className="error">{error}</div>}
          <form onSubmit={onSend} className="composer">
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder={t.placeholder} />
            <button className="btn" disabled={busy || !input.trim()}>{t.send}</button>
          </form>
        </section>
      </main>
    </div>
  );
}
