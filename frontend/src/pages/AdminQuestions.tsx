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
  const [editingQuestion, setEditingQuestion] = useState<QuestionVariant | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expanded, setExpanded] = useState<string | null>(null);
  const [filterLang, setFilterLang] = useState<string>('ja');
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

  const handleEdit = (groupId: string, lang: string) => {
    const group = questions.find(g => g.group_id === groupId);
    if (!group) return;
    const rec = group.translations.find(tr => tr.language === lang);
    if (rec) setEditingQuestion({ ...rec });
  };

  const saveEdit = async () => {
    if (!editingQuestion) return;
    setStatus('saving');
    await fetch(`${apiBase}/admin/questions/${editingQuestion.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Token': token },
      body: JSON.stringify(editingQuestion)
    });
    setEditingQuestion(null);
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
        {status && (
          <div className="alert alert-info text-sm">{status}</div>
        )}
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
            <div className="flex items-center space-x-2 mb-2">
              <button className="btn btn-error btn-sm" onClick={removeSelected}>Delete Selected</button>
              <select
                className="select select-bordered select-sm"
                value={filterLang}
                onChange={e => setFilterLang(e.target.value)}
              >
                {LANGS.map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
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
              {questions
                .sort((a,b)=>a.id-b.id)
                .filter(q => filterLang === 'ja' || q.translations.some(t => t.language === filterLang))
                .map((q, idx) => {
                  const variant = filterLang === 'ja' ? q : q.translations.find(t => t.language === filterLang)!;
                  return (
                    <React.Fragment key={q.group_id}>
                      <tr>
                        <td><input type="checkbox" className="checkbox" checked={selected.has(variant.id)} onChange={e => {
                          const s = new Set(selected);
                          if (e.target.checked) q.translations.forEach(t => s.add(t.id)); else q.translations.forEach(t => s.delete(t.id));
                          setSelected(s);
                        }} /></td>
                        <td>{idx + 1}</td>
                        <td className="truncate max-w-xs" title={variant.question}>{variant.question}</td>
                        <td className="truncate max-w-xs" title={variant.options[0]}>{variant.options[0]}</td>
                        <td className="truncate max-w-xs" title={variant.options[1]}>{variant.options[1]}</td>
                        <td className="truncate max-w-xs" title={variant.options[2]}>{variant.options[2]}</td>
                        <td className="truncate max-w-xs" title={variant.options[3]}>{variant.options[3]}</td>
                        <td>{variant.answer}</td>
                        <td className="space-x-2">
                          <button className="btn btn-xs" onClick={() => setExpanded(expanded === q.group_id ? null : q.group_id)}>Langs</button>
                          <button className="btn btn-xs" onClick={() => handleEdit(q.group_id, variant.language)}>Edit</button>
                          <button className="btn btn-xs btn-error" onClick={() => remove(variant.id)}>Delete</button>
                        </td>
                      </tr>
                      {expanded === q.group_id && (
                        <tr className="bg-base-200">
                          <td></td>
                          <td colSpan={8}>
                            <div className="flex flex-wrap gap-2 py-2">
                              {q.translations.filter(t => t.language !== variant.language).map(tr => (
                                <button
                                  key={tr.language}
                                  className="btn btn-xs"
                                  onClick={() => handleEdit(q.group_id, tr.language)}
                                >
                                  {tr.language}: {tr.question.slice(0, 30)}
                                </button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
            </tbody>
            </table>
          </>
        )}
        {editingQuestion && (
          <dialog open className="modal">
            <div className="modal-box space-y-2">
              <h3 className="font-bold">Edit ({editingQuestion.language}) ID {editingQuestion.id}</h3>
              <textarea
                className="textarea textarea-bordered w-full"
                value={editingQuestion.question}
                onChange={e => setEditingQuestion({ ...editingQuestion, question: e.target.value })}
              />
              {editingQuestion.options.map((opt, idx) => (
                <input
                  key={idx}
                  className="input input-bordered w-full"
                  value={opt}
                  onChange={e => {
                    const opts = editingQuestion.options.slice();
                    opts[idx] = e.target.value;
                    setEditingQuestion({ ...editingQuestion, options: opts });
                  }}
                />
              ))}
              <input
                type="number"
                className="input input-bordered w-full"
                value={editingQuestion.answer}
                onChange={e => setEditingQuestion({ ...editingQuestion, answer: Number(e.target.value) })}
              />
              <input
                type="number"
                className="input input-bordered w-full"
                value={editingQuestion.irt_a}
                onChange={e => setEditingQuestion({ ...editingQuestion, irt_a: Number(e.target.value) })}
              />
              <input
                type="number"
                className="input input-bordered w-full"
                value={editingQuestion.irt_b}
                onChange={e => setEditingQuestion({ ...editingQuestion, irt_b: Number(e.target.value) })}
              />
              <input
                type="text"
                className="input input-bordered w-full"
                value={editingQuestion.image_prompt || ''}
                onChange={e => setEditingQuestion({ ...editingQuestion, image_prompt: e.target.value })}
              />
              <input
                type="text"
                className="input input-bordered w-full"
                value={editingQuestion.image || ''}
                onChange={e => setEditingQuestion({ ...editingQuestion, image: e.target.value })}
                placeholder="Image URL (optional)"
              />
              <div className="modal-action">
                <button className="btn" onClick={saveEdit} disabled={status==='saving'}>Save</button>
                <button className="btn" onClick={() => setEditingQuestion(null)}>Cancel</button>
              </div>
            </div>
          </dialog>
        )}
      </div>
    </Layout>
  );
}
