import React, { useEffect, useState, useRef } from 'react';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

const LANGS = Object.keys(i18n.options.resources);

interface QuestionVariant {
  id: number;
  group_id: string;
  language: string;
  question: string;
  options: string[];
  answer: number;
  irt_a: number;
  irt_b: number;
  image_prompt?: string | null;
  image?: string | null;
}

interface QuestionGroup extends QuestionVariant {
  translations: QuestionVariant[];
}

export default function AdminQuestions() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('adminToken') || '');
  const [questions, setQuestions] = useState<QuestionGroup[]>([]);
  const [editing, setEditing] = useState<QuestionGroup | null>(null);
  const [editForms, setEditForms] = useState<Record<string, QuestionVariant>>({});
  const [status, setStatus] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
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
    setStatus('loading');
    const res = await fetch(`${apiBase}/admin/questions`, {
      headers: { 'X-Admin-Token': token }
    });
    if (res.ok) {
      const data = await res.json();
      const groups: Record<string, QuestionGroup> = {};
      data.sort((a: any, b: any) => a.id - b.id).forEach((item: any) => {
        const variant: QuestionVariant = item;
        if (!groups[item.group_id]) {
          groups[item.group_id] = { ...variant, translations: [variant] };
        } else {
          groups[item.group_id].translations.push(variant);
          if (variant.language === 'ja') {
            Object.assign(groups[item.group_id], variant);
          }
        }
      });
      setQuestions(Object.values(groups).sort((a, b) => a.id - b.id));
    }
    setStatus(null);
  };

  useEffect(() => { fetchQuestions(); }, [token]);

  const startEdit = (q: QuestionGroup) => {
    const forms: Record<string, QuestionVariant> = {};
    q.translations.forEach(tr => {
      forms[tr.language] = { ...tr };
    });
    setEditing(q);
    setEditForms(forms);
  };

  const submitEdit = async () => {
    if (!editing) return;
    setStatus('saving');
    for (const lang of Object.keys(editForms)) {
      const form = editForms[lang];
      if (!Array.isArray(form.options) || form.options.length !== 4) continue;
      await fetch(`${apiBase}/admin/questions/${form.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': token
        },
        body: JSON.stringify(form)
      });
    }
    setEditing(null);
    setStatus(null);
    await fetchQuestions();
  };

  const remove = async (id: number) => {
    if (!confirm('Delete this question?')) return;
    await fetch(`${apiBase}/admin/questions/${id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Token': token }
    });
    setQuestions(q => q.filter(item => item.id !== id));
  };

  const removeSelected = async () => {
    const ids = Array.from(selected);
    if (!ids.length) return;
    if (!confirm('Delete selected questions?')) return;
    setStatus('deleting');
    await fetch(`${apiBase}/admin/questions/delete_batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
      body: JSON.stringify(ids)
    });
    setQuestions(q => q.filter(item => !item.translations.some(t => ids.includes(t.id))));
    setSelected(new Set());
    setStatus(null);
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
            <button className="btn btn-error btn-sm mb-2" onClick={removeSelected}>Delete Selected</button>
            <table className="table w-full">
            <thead>
              <tr>
                <th></th>
                <th>#</th>
                <th>Question</th>
                <th>A1</th>
                <th>A2</th>
                <th>A3</th>
                <th>A4</th>
                <th>Ans</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {questions.sort((a,b)=>a.id-b.id).map((q, idx) => (
                <tr key={q.id}>
                  <td><input type="checkbox" className="checkbox" checked={selected.has(q.id)} onChange={e => {
                    const s = new Set(selected);
                    if (e.target.checked) q.translations.forEach(t => s.add(t.id)); else q.translations.forEach(t => s.delete(t.id));
                    setSelected(s);
                  }} /></td>
                  <td>{idx + 1}</td>
                  <td className="truncate max-w-xs" title={q.question}>{q.question}</td>
                  <td className="truncate max-w-xs" title={q.options[0]}>{q.options[0]}</td>
                  <td className="truncate max-w-xs" title={q.options[1]}>{q.options[1]}</td>
                  <td className="truncate max-w-xs" title={q.options[2]}>{q.options[2]}</td>
                  <td className="truncate max-w-xs" title={q.options[3]}>{q.options[3]}</td>
                  <td>{q.answer}</td>
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
          <div className="space-y-4 p-4 border rounded">
            <h3 className="font-bold">Edit Question {editing.id}</h3>
            {Object.values(editForms).map(form => (
              <div key={form.language} className="space-y-2 border p-2">
                <h4 className="font-semibold">{form.language}</h4>
                <select
                  className="select select-bordered"
                  value={form.language}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, language: e.target.value }
                  })}
                >
                  {LANGS.map(l => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
                <textarea
                  className="textarea textarea-bordered w-full"
                  value={form.question}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, question: e.target.value }
                  })}
                />
                {form.options.map((opt, idx) => (
                  <input
                    key={idx}
                    className="input input-bordered w-full"
                    value={opt}
                    onChange={e => {
                      const opts = form.options.slice();
                      opts[idx] = e.target.value;
                      setEditForms({
                        ...editForms,
                        [form.language]: { ...form, options: opts }
                      });
                    }}
                  />
                ))}
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={form.answer}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, answer: Number(e.target.value) }
                  })}
                />
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={form.irt_a}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, irt_a: Number(e.target.value) }
                  })}
                />
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={form.irt_b}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, irt_b: Number(e.target.value) }
                  })}
                />
                <input
                  type="text"
                  className="input input-bordered w-full"
                  value={form.image_prompt || ''}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, image_prompt: e.target.value }
                  })}
                />
                <input
                  type="text"
                  className="input input-bordered w-full"
                  value={form.image || ''}
                  onChange={e => setEditForms({
                    ...editForms,
                    [form.language]: { ...form, image: e.target.value }
                  })}
                  placeholder="Image URL (optional)"
                />
              </div>
            ))}
            <div className="space-x-2">
              <button className="btn" onClick={submitEdit} disabled={status==='saving'}>Save</button>
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
