import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';

function ConfidenceBadge({ score }) {
  let cls = 'low';
  if (score >= 70) cls = 'high';
  else if (score >= 40) cls = 'medium';
  return <span className={`badge ${cls}`}>{score}%</span>;
}

export default function QuestionnaireView() {
  const { runId } = useParams();
  const [run, setRun] = useState(null);
  const [error, setError] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState('');
  const [actionLoading, setActionLoading] = useState('');

  useEffect(() => {
    loadRun();
  }, [runId]);

  async function loadRun() {
    try {
      const data = await api.getRun(runId);
      setRun(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRegenerate(questionId) {
    setActionLoading(questionId);
    try {
      await api.regenerate(questionId);
      await loadRun();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading('');
    }
  }

  async function handleSaveEdit(answerId) {
    setActionLoading(answerId);
    try {
      await api.editAnswer(answerId, editText);
      setEditingId(null);
      await loadRun();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading('');
    }
  }

  async function handleExport(format) {
    try {
      const blob = await api.exportRun(runId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `answers_${runId.slice(0, 8)}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!run) return <p className="loading">Loading run...</p>;

  return (
    <div>
      <div className="flex-between mb-2">
        <div>
          <Link to="/dashboard">← Back to Dashboard</Link>
          <h2 className="mt-1">Run {run.id.slice(0, 8)}…</h2>
          <p style={{ fontSize: 13, color: 'var(--muted)' }}>{run.created_at}</p>
        </div>
        <div className="flex">
          <button onClick={() => handleExport('xlsx')}>Export XLSX</button>
          <button className="secondary" onClick={() => handleExport('pdf')}>Export PDF</button>
        </div>
      </div>

      {run.answers.map((a) => (
        <div key={a.answer_id} className="card">
          <div className="flex-between">
            <h3>
              Q{a.question_index}: {a.question_text}
            </h3>
            <ConfidenceBadge score={a.confidence_score} />
          </div>

          {editingId === a.answer_id ? (
            <div className="mt-1">
              <textarea
                rows={4}
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
              />
              <div className="flex">
                <button
                  className="success"
                  onClick={() => handleSaveEdit(a.answer_id)}
                  disabled={actionLoading === a.answer_id}
                >
                  Save
                </button>
                <button className="secondary" onClick={() => setEditingId(null)}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="mt-1">
              <p>{a.answer_text}</p>
              {a.is_edited && (
                <span className="badge medium" style={{ marginTop: 4 }}>Edited</span>
              )}
            </div>
          )}

          {/* Citations */}
          {a.citations && a.citations.length > 0 && (
            <div className="mt-1" style={{ fontSize: 13 }}>
              <strong>Citations:</strong>{' '}
              {a.citations.map((c, i) => (
                <span key={i} style={{ color: 'var(--primary)' }}>
                  [{c}]{i < a.citations.length - 1 ? ', ' : ''}
                </span>
              ))}
            </div>
          )}

          {/* Evidence Snippets */}
          {a.evidence_snippets && a.evidence_snippets.length > 0 && (
            <details className="mt-1">
              <summary style={{ cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                Evidence Snippets
              </summary>
              {a.evidence_snippets.map((s, i) => (
                <div key={i} className="snippet">{s}</div>
              ))}
            </details>
          )}

          {/* Actions */}
          <div className="flex mt-1">
            <button
              className="secondary"
              onClick={() => {
                setEditingId(a.answer_id);
                setEditText(a.answer_text);
              }}
              style={{ fontSize: 12, padding: '4px 10px' }}
            >
              ✏️ Edit
            </button>
            <button
              className="secondary"
              onClick={() => handleRegenerate(a.question_id)}
              disabled={!!actionLoading}
              style={{ fontSize: 12, padding: '4px 10px' }}
            >
              {actionLoading === a.question_id ? <><span className="spinner"></span>Regenerating…</> : '🔄 Regenerate'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
