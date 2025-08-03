import React, { useEffect, useState, useRef } from 'react';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
const languageOptions = ['ja', 'en', 'tr', 'ru', 'zh', 'ko', 'es', 'fr', 'it', 'de', 'ar'];

interface QuestionVariant {
  id: number;
  group_id: string;
  lang: string;
  question: string;
  options: string[];
  answer: number;
  irt_a: number;
  irt_b: number;
  image_prompt?: string | null;
  image?: string | null;
  approved: boolean;
}

interface QuestionGroup {
  base: QuestionVariant | null;
  translations: QuestionVariant[];
}

export default function AdminQuestions() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('adminToken') || '');
  const [allQuestions, setAllQuestions] = useState<QuestionVariant[]>([]);
  const [displayedQuestions, setDisplayedQuestions] = useState<QuestionVariant[]>([]);
  const [selectedLang, setSelectedLang] = useState<string>('ja');
  const [editingQuestion, setEditingQuestion] = useState<QuestionVariant | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expanded, setExpanded] = useState<string | null>(null);
  const jsonRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLInputElement>(null);
  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [imageFiles, setImageFiles] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const { t } = useTranslation();

  const apiBase = import.meta.env.VITE_API_BASE || '';
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
  }

  const filterByLanguage = (data: QuestionVariant[], lang: string) =>
    lang === 'ja' ? data : data.filter(q => q.lang === lang);

  const fetchQuestions = async (lang: string): Promise<QuestionVariant[]> => {
    if (!token) return [];
    setStatus('loading');
    const res = await fetch(`${apiBase}/admin/questions/?lang=${lang}`, {
      headers: { 'X-Admin-Api-Key': token },
      redirect: 'manual'
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return [];
    }
    let sorted: QuestionVariant[] = [];
    if (res.ok) {
      const data = await res.json();
      sorted = data.sort((a: any, b: any) => a.id - b.id);
      setAllQuestions(sorted);
      setDisplayedQuestions(filterByLanguage(sorted, lang));
    }
    setStatus(null);
    return sorted;
  };

  useEffect(() => { if (token) fetchQuestions(selectedLang); }, [token, selectedLang]);

  const handleLangChange = (lang: string) => {
    setSelectedLang(lang);
  };

  const grouped = Object.values(
    displayedQuestions.reduce<Record<string, QuestionGroup>>((acc, q) => {
      acc[q.group_id] = acc[q.group_id] || { base: null, translations: [] };
      if (q.lang === 'ja') acc[q.group_id].base = q;
      else acc[q.group_id].translations.push(q);
      return acc;
    }, {})
  );

  const handleEdit = (groupId: string, lang: string = 'ja') => {
    const record = allQuestions.find(q => q.group_id === groupId && q.lang === lang);
    if (record) {
      setEditingQuestion({ ...record });
      setIsEditModalOpen(true);
    }
  };

  const saveEdit = async () => {
    if (!editingQuestion) return;
    setStatus('saving');
    const res = await fetch(`${apiBase}/admin/questions/${editingQuestion.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify(editingQuestion)
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    setEditingQuestion(null);
    setIsEditModalOpen(false);
    setStatus(null);
    await fetchQuestions(selectedLang);
  };

  const remove = async (id: number) => {
    if (!confirm('Delete this question?')) return;
    const res = await fetch(`${apiBase}/admin/questions/${id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    await fetchQuestions(selectedLang);
  };

  const removeSelected = async () => {
    const ids = Array.from(selected);
    if (!ids.length) return;
    if (!confirm('Delete selected questions?')) return;
    setStatus('deleting');
    const res = await fetch(`${apiBase}/admin/questions/delete_batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify(ids)
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    setSelected(new Set());
    setStatus(null);
    await fetchQuestions(selectedLang);
  };

  const toggleApprove = async (groupId: string) => {
    const res = await fetch(`${apiBase}/admin/questions/${groupId}/toggle_approved`, {
      method: 'POST',
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    if (res.ok) {
      const data = await res.json();
      const updated = allQuestions.map(q =>
        q.group_id === groupId ? { ...q, approved: data.approved } : q
      );
      setAllQuestions(updated);
      setDisplayedQuestions(filterByLanguage(updated, selectedLang));
    }
  };

  const removeAll = async () => {
    if (
      window.confirm('Delete ALL questions? This cannot be undone.') &&
      window.confirm('Are you absolutely sure?')
    ) {
      setStatus('deleting');
      const res = await fetch(`${apiBase}/admin/questions/delete_all`, {
        method: 'POST',
        headers: { 'X-Admin-Api-Key': token },
      });
      if (res.status === 401) {
        setStatus('Invalid admin API key. Please check your settings.');
        return;
      }
      setStatus(null);
      await fetchQuestions(selectedLang);
    }
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
      headers: { 'X-Admin-Api-Key': token },
      body: formData
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      setUploadStatus(null);
      setIsImporting(false);
      return;
    }
    setUploadStatus('translating');
    const data = await res.json();
    if (res.ok) {
      setUploadStatus('saving');
      await fetchQuestions('ja');
      setSelectedLang('ja');
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
    fetchQuestions(selectedLang);
  };

  return (
    <Layout>
      <div className="space-y-4 max-w-xl mx-auto">
        <nav className="tabs">
          <Link to="/admin/questions" className="tab tab-bordered tab-active">Questions</Link>
          <Link to="/admin/surveys" className="tab tab-bordered">Surveys</Link>
          <Link to="/admin/users" className="tab tab-bordered">Users</Link>
        </nav>
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
        {allQuestions.length > 0 && (
          <>
        <div className="flex items-center space-x-2 mb-2">
          <button className="btn btn-error btn-sm" onClick={removeSelected}>Delete Selected</button>
          <button className="btn btn-error btn-sm" onClick={removeAll}>Delete All Questions</button>
          <select
            className="select select-bordered select-sm"
            value={selectedLang}
            onChange={e => handleLangChange(e.target.value)}
          >
            {languageOptions.map(l => (
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
                <th>Approved</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {grouped.map((g, idx) => {
                const variant =
                  selectedLang === 'ja'
                    ? g.base!
                    : g.translations.find(t => t.lang === selectedLang)!;
                const groupRecords = allQuestions.filter(
                  q => q.group_id === (g.base?.group_id || g.translations[0].group_id)
                );
                const ids = groupRecords.map(r => r.id);
                const checked = ids.every(id => selected.has(id));
                const otherLangs = groupRecords.filter(r => r.lang !== variant.lang);
                const approved = groupRecords[0]?.approved;
                return (
                  <React.Fragment key={variant.group_id}>
                    <tr>
                      <td>
                        <input
                          type="checkbox"
                          className="checkbox"
                          checked={checked}
                          onChange={e => {
                            const s = new Set(selected);
                            ids.forEach(id => {
                              if (e.target.checked) s.add(id);
                              else s.delete(id);
                            });
                            setSelected(s);
                          }}
                        />
                      </td>
                      <td>{idx + 1}</td>
                      <td className="truncate max-w-xs" title={variant.question}>{variant.question}</td>
                      <td className="truncate max-w-xs" title={variant.options[0]}>{variant.options[0]}</td>
                      <td className="truncate max-w-xs" title={variant.options[1]}>{variant.options[1]}</td>
                      <td className="truncate max-w-xs" title={variant.options[2]}>{variant.options[2]}</td>
                      <td className="truncate max-w-xs" title={variant.options[3]}>{variant.options[3]}</td>
                      <td>{variant.answer}</td>
                      <td>{approved ? '✓' : ''}</td>
                      <td className="space-x-2">
                        <button
                          className="btn btn-xs"
                          onClick={() =>
                            setExpanded(expanded === variant.group_id ? null : variant.group_id)
                          }
                        >
                          Other Languages ▼
                        </button>
                        <button className="btn btn-xs" onClick={() => handleEdit(variant.group_id, variant.lang)}>
                          Edit
                        </button>
                        <button className="btn btn-xs" onClick={() => toggleApprove(variant.group_id)}>
                          {approved ? 'Unapprove' : 'Approve'}
                        </button>
                        <button className="btn btn-xs btn-error" onClick={() => remove(variant.id)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                    {expanded === variant.group_id && otherLangs.length > 0 && (
                      <tr className="bg-base-200">
                        <td></td>
                        <td colSpan={9}>
                          <div className="flex flex-wrap gap-2 py-2">
                            {otherLangs.map(tr => (
                              <button
                                key={tr.lang}
                                className="btn btn-xs"
                                onClick={() => handleEdit(variant.group_id, tr.lang)}
                              >
                                {tr.lang}
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
        {isEditModalOpen && editingQuestion && (
          <dialog open className="modal">
            <div className="modal-box space-y-2">
              <h3 className="font-bold mb-2">Edit ({editingQuestion.lang}) ID {editingQuestion.id}</h3>
              <label className="form-control w-full">
                <span className="label-text">Question</span>
                <textarea
                  className="textarea textarea-bordered"
                  value={editingQuestion.question}
                  onChange={e => setEditingQuestion({ ...editingQuestion, question: e.target.value })}
                />
              </label>
              {editingQuestion.options.map((opt, idx) => (
                <label className="form-control w-full" key={idx}>
                  <span className="label-text">Option {idx + 1}</span>
                  <input
                    type="text"
                    className="input input-bordered"
                    value={opt}
                    onChange={e => {
                      const opts = editingQuestion.options.slice();
                      opts[idx] = e.target.value;
                      setEditingQuestion({ ...editingQuestion, options: opts });
                    }}
                  />
                </label>
              ))}
              <label className="form-control w-full">
                <span className="label-text">Correct answer index (0–3)</span>
                <input
                  type="number"
                  className="input input-bordered"
                  value={editingQuestion.answer}
                  onChange={e => setEditingQuestion({ ...editingQuestion, answer: Number(e.target.value) })}
                />
              </label>
              <label className="form-control w-full">
                <span className="label-text">IRT a</span>
                <input
                  type="number"
                  step="0.01"
                  className="input input-bordered"
                  value={editingQuestion.irt_a}
                  onChange={e => setEditingQuestion({ ...editingQuestion, irt_a: Number(e.target.value) })}
                />
              </label>
              <label className="form-control w-full">
                <span className="label-text">IRT b</span>
                <input
                  type="number"
                  step="0.01"
                  className="input input-bordered"
                  value={editingQuestion.irt_b}
                  onChange={e => setEditingQuestion({ ...editingQuestion, irt_b: Number(e.target.value) })}
                />
              </label>
              <label className="form-control w-full">
                <span className="label-text">Image URL (optional)</span>
                <input
                  type="text"
                  className="input input-bordered"
                  value={editingQuestion.image || ''}
                  onChange={e => setEditingQuestion({ ...editingQuestion, image: e.target.value })}
                />
              </label>
              <div className="modal-action">
                <button className="btn" onClick={saveEdit} disabled={status==='saving'}>Save</button>
                <button className="btn" onClick={() => { setIsEditModalOpen(false); setEditingQuestion(null); }}>Cancel</button>
              </div>
            </div>
          </dialog>
        )}
      </div>
    </Layout>
  );
}
