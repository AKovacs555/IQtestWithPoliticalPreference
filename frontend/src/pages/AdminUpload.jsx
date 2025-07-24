import React, { useState } from 'react';
import Layout from '../components/Layout';

export default function AdminUpload() {
  const [jsonText, setJsonText] = useState('');
  const [apiKey, setApiKey] = useState(import.meta.env.VITE_ADMIN_KEY || '');
  const [status, setStatus] = useState('');
  const [bankInfo, setBankInfo] = useState(null);
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
    let parsed;
    try {
      parsed = JSON.parse(jsonText || '[]');
      setJsonValid(true);
    } catch {
      setJsonValid(false);
      setStatus('Invalid JSON');
      return;
    }

    const questions = Array.isArray(parsed) ? parsed : parsed.questions;
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE}/admin/upload-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Api-Key': apiKey,
        },
        body: JSON.stringify({ questions }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || res.statusText);
      }
      setStatus(data.log || 'Success');
      fetchInfo();
    } catch (err) {
      setStatus('Error: ' + err.message);
    }
  };

  const fetchInfo = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE}/admin/question-bank-info`, {
        headers: { 'X-Admin-Api-Key': apiKey }
      });
      if (res.ok) {
        const info = await res.json();
        setBankInfo(info);
      }
    } catch {}
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
        {bankInfo && (
          <p>Current questions in bank: {bankInfo.count}</p>
        )}
      </div>
    </Layout>
  );
}
