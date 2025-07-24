import React, { useState } from 'react';
import Layout from '../components/Layout';

export default function AdminUpload() {
  const [jsonText, setJsonText] = useState('');
  const [apiKey, setApiKey] = useState(import.meta.env.VITE_ADMIN_KEY || '');
  const [status, setStatus] = useState('');
  const [jsonValid, setJsonValid] = useState(true);

  const handleFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      handleJsonChange(ev.target.result);
    };
    reader.readAsText(file);
  };

  const handleJsonChange = (val) => {
    setJsonText(val);
    try {
      JSON.parse(val || '[]');
      setJsonValid(true);
    } catch {
      setJsonValid(false);
    }
  };

  const submit = async () => {
    try {
      const data = JSON.parse(jsonText || '[]');
      const questions = Array.isArray(data) ? data : data.questions;
      const res = await fetch(`${import.meta.env.VITE_API_BASE}/admin/upload-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Api-Key': apiKey,
        },
        body: JSON.stringify({ questions }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || res.statusText);
      }
      const info = await res.json();
      setStatus(`Uploaded ${info.count} questions`);
    } catch (err) {
      setStatus('Error: ' + err.message);
    }
  };

  return (
    <Layout>
      <div className="space-y-4 max-w-xl mx-auto">
        <h2 className="text-xl font-bold">Upload Questions</h2>
        <textarea
          className="textarea textarea-bordered w-full h-40"
          value={jsonText}
          onChange={(e) => handleJsonChange(e.target.value)}
        />
        <input type="file" accept="application/json" onChange={handleFile} className="file-input file-input-bordered w-full" />
        <input
          type="text"
          className="input input-bordered w-full"
          placeholder="Admin API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
        <button className="btn btn-primary" onClick={submit} disabled={!jsonValid}>
          Upload
        </button>
        {!jsonValid && (
          <p className="text-red-500">Invalid JSON</p>
        )}
        {status && <p>{status}</p>}
      </div>
    </Layout>
  );
}
