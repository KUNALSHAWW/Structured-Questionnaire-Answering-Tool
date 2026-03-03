import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function Dashboard() {
  const [questionnaires, setQuestionnaires] = useState([]);
  const [references, setReferences] = useState([]);
  const [runs, setRuns] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const refresh = useCallback(async () => {
    try {
      const [qs, refs, rs] = await Promise.all([
        api.listQuestionnaires(),
        api.listReferences(),
        api.listRuns(),
      ]);
      setQuestionnaires(qs);
      setReferences(refs);
      setRuns(rs);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleUploadQ(e) {
    const file = e.target.files[0];
    if (!file) return;
    setStatus('Uploading questionnaire...');
    setError('');
    try {
      const data = await api.uploadQuestionnaire(file);
      setStatus(`Parsed ${data.num_questions} questions from ${data.filename}`);
      refresh();
    } catch (err) {
      setError(err.message);
    }
    e.target.value = '';
  }

  async function handleUploadRef(e) {
    const file = e.target.files[0];
    if (!file) return;
    setStatus('Uploading reference...');
    setError('');
    try {
      const data = await api.uploadReference(file);
      setStatus(`Reference uploaded: ${data.filename} (${data.text_length} chars)`);
      refresh();
    } catch (err) {
      setError(err.message);
    }
    e.target.value = '';
  }

  async function handleBuildIndex() {
    setLoading(true);
    setStatus('Building index (this may take a moment)...');
    setError('');
    try {
      const data = await api.buildIndex();
      setStatus(`Index built: ${data.num_passages} passages, ${data.num_vectors} vectors`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate(qid) {
    setLoading(true);
    setStatus('Generating answers...');
    setError('');
    try {
      const data = await api.generate(qid);
      setStatus(`Generated ${data.num_answers} answers`);
      refresh();
      navigate(`/questionnaire/${data.run_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="mb-2">Dashboard</h2>

      {error && <p className="error">{error}</p>}
      {status && <p style={{ color: 'var(--success)', marginBottom: 12 }}>{status}</p>}

      {/* Upload Section */}
      <div className="card">
        <h3>Upload Files</h3>
        <div className="flex mt-1">
          <div>
            <label><strong>Questionnaire</strong> (PDF/XLSX/TXT)</label>
            <input type="file" accept=".pdf,.xlsx,.txt" onChange={handleUploadQ} />
          </div>
          <div>
            <label><strong>Reference Document</strong> (PDF/TXT/CSV/DOCX)</label>
            <input type="file" accept=".pdf,.txt,.csv,.docx" onChange={handleUploadRef} />
          </div>
        </div>
      </div>

      {/* Build Index */}
      <div className="card">
        <div className="flex-between">
          <div>
            <h3>Build Index</h3>
            <p style={{ fontSize: 13, color: 'var(--muted)' }}>
              Process references into passages and build embeddings for retrieval.
            </p>
          </div>
          <button onClick={handleBuildIndex} disabled={loading || references.length === 0}>
            {loading ? 'Building...' : 'Build Index'}
          </button>
        </div>
      </div>

      {/* Questionnaires */}
      <div className="card">
        <h3>Questionnaires</h3>
        {questionnaires.length === 0 ? (
          <p className="loading">No questionnaires uploaded yet.</p>
        ) : (
          questionnaires.map((q) => (
            <div key={q.id} className="flex-between mt-1" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
              <span>
                <strong>{q.filename}</strong> — {q.num_questions} questions
              </span>
              <button onClick={() => handleGenerate(q.id)} disabled={loading}>
                Generate Answers
              </button>
            </div>
          ))
        )}
      </div>

      {/* References */}
      <div className="card">
        <h3>References ({references.length})</h3>
        {references.map((r) => (
          <div key={r.id} className="mt-1">
            📄 {r.filename} <span style={{ color: 'var(--muted)', fontSize: 12 }}>({r.file_type})</span>
          </div>
        ))}
      </div>

      {/* Previous Runs */}
      <div className="card">
        <h3>Previous Runs</h3>
        {runs.length === 0 ? (
          <p className="loading">No runs yet.</p>
        ) : (
          runs.map((r) => (
            <div key={r.id} className="flex-between mt-1" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 8 }}>
              <span>
                Run {r.id.slice(0, 8)}… — {r.num_answers} answers —{' '}
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>{r.created_at}</span>
              </span>
              <button className="secondary" onClick={() => navigate(`/questionnaire/${r.id}`)}>
                View
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
