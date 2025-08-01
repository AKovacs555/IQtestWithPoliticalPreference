import React, { useEffect, useState, useRef } from 'react';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';

interface Question {
  id: number;
  question: string;
  options: string[];
  answer: number;
  irt_a: number;
  irt_b: number;
  image_prompt?: string | null;
  image?: string | null;
}

export default function AdminQuestions() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('adminToken') || '');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [editing, setEditing] = useState<Question | null>(null);
  const [form, setForm] = useState<Partial<Question>>({});
  const jsonRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLInputElement>(null);
  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [imageFiles, setImageFiles] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const { t } = useTranslation();

  const apiBase = import.meta.env.VITE_API_BASE;

  const fetchQuestions = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/questions`, {
      headers: { 'X-Admin-Token': token }
    });
    if (res.ok) {
      const data = await res.json();
      setQuestions(data);
    }
  };

  useEffect(() => { fetchQuestions(); }, [token]);

  const startEdit = (q: Question) => {
    setEditing(q);
    setForm({ ...q });
  };

  const submitEdit = async () => {
    if (!editing) return;
    if (!Array.isArray(form.options) || form.options.length !== 4) {
      alert('Options must be 4 items');
      return;
    }
    const res = await fetch(`${apiBase}/admin/questions/${editing.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': token
      },
      body: JSON.stringify(form)
    });
    if (res.ok) {
      setEditing(null);
      await fetchQuestions();
    } else {
      const data = await res.json();
      alert(data.detail || 'Error');
    }
  };

  const remove = async (id: number) => {
    if (!confirm('Delete this question?')) return;
    await fetch(`${apiBase}/admin/questions/${id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Token': token }
    });
    setQuestions(q => q.filter(item => item.id !== id));
  };

  const handleJsonChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setJsonFile(e.target.files?.[0] || null);
  };

  const handleImagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setImageFiles(e.target.files);
  };

  const handleImport = async () => {
    if (!jsonFile) {
      alert('Please select a JSON file');
      return;
    }
    setIsImporting(true);
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append('json_file', jsonFile);
    if (imageFiles) {
      Array.from(imageFiles).forEach(file => {
        formData.append('images', file);
      });
    }
    const res = await fetch(`${apiBase}/admin/import_questions_with_images`, {
      method: 'POST',
      headers: { 'X-Admin-Token': token },
      body: formData
    });
    setUploadStatus('translating');
    const data = await res.json();
    if (res.ok) {
      setUploadStatus('saving');
      await fetchQuestions();
      setUploadStatus(null);
      setIsImporting(false);
      alert(`Imported ${data.inserted}`);
    } else {
      setUploadStatus(null);
      setIsImporting(false);
      alert(data.detail || 'Error');
    }
    setJsonFile(null);
    setImageFiles(null);
    if (jsonRef.current) jsonRef.current.value = '';
    if (imgRef.current) imgRef.current.value = '';
  };

  const handleLogin = () => {
    localStorage.setItem('adminToken', token);
    fetchQuestions();
  };

  return (
    <Layout>
      <div className="space-y-4">
        <div className="space-y-2">
          <input
            type="text"
            className="input input-bordered"
            placeholder="Admin Token"
            value={token}
            onChange={e => setToken(e.target.value)}
          />
          <button className="btn" onClick={handleLogin}>Load Questions</button>
        </div>
        {token && (
          <div className="space-y-2">
            <div className="space-y-1">
              <input type="file" accept="application/json" ref={jsonRef} onChange={handleJsonChange} />
              <input type="file" multiple ref={imgRef} onChange={handleImagesChange} />
            </div>
            <button className="btn" onClick={handleImport} disabled={isImporting}>Import Questions</button>
            {isImporting && uploadStatus && (
              <div className="alert alert-info text-sm">
                {t(`upload.status.${uploadStatus}`)}
              </div>
            )}
          </div>
        )}
        {questions.length > 0 && (
          <>
            <table className="table w-full">
            <thead>
              <tr>
                <th>ID</th>
                <th>Question</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {questions.map(q => (
                <tr key={q.id}>
                  <td>{q.id}</td>
                  <td>{q.question}</td>
                  <td className="space-x-2">
                    <button className="btn btn-sm" onClick={() => startEdit(q)}>Edit</button>
                    <button className="btn btn-sm btn-error" onClick={() => remove(q.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
            </table>
          </>
        )}
        {editing && (
          <div className="space-y-2">
            <h3 className="font-bold">Edit Question {editing.id}</h3>
            <textarea
              className="textarea textarea-bordered w-full"
              value={form.question || ''}
              onChange={e => setForm({ ...form, question: e.target.value })}
            />
            {form.options?.map((opt, idx) => (
              <input
                key={idx}
                className="input input-bordered w-full"
                value={opt}
                onChange={e => {
                  const opts = form.options!.slice();
                  opts[idx] = e.target.value;
                  setForm({ ...form, options: opts });
                }}
              />
            ))}
            <input
              type="number"
              className="input input-bordered w-full"
              value={form.answer ?? 0}
              onChange={e => setForm({ ...form, answer: Number(e.target.value) })}
            />
            <input
              type="number"
              className="input input-bordered w-full"
              value={form.irt_a ?? 1}
              onChange={e => setForm({ ...form, irt_a: Number(e.target.value) })}
            />
            <input
              type="number"
              className="input input-bordered w-full"
              value={form.irt_b ?? 0}
              onChange={e => setForm({ ...form, irt_b: Number(e.target.value) })}
            />
            <input
              type="text"
              className="input input-bordered w-full"
              value={form.image_prompt || ''}
              onChange={e => setForm({ ...form, image_prompt: e.target.value })}
            />
            <input
              type="text"
              className="input input-bordered w-full"
              value={form.image || ''}
              onChange={e => setForm({ ...form, image: e.target.value })}
              placeholder="Image URL (optional)"
            />
            <div className="space-x-2">
              <button className="btn" onClick={submitEdit}>Save</button>
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
