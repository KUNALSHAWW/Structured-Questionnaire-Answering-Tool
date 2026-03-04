/* Thin API wrapper */
const rawBase = import.meta.env.VITE_API_URL || '';
const BASE = rawBase ? `${rawBase.replace(/\/+$/, '')}/api` : '/api';

function getToken() {
  return localStorage.getItem('token');
}

async function request(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  // Don't set Content-Type for FormData (browser sets boundary)
  if (!(opts.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  // Handle file downloads
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/vnd.openxmlformats') || ct.includes('application/pdf')) {
    return res.blob();
  }

  return res.json();
}

export const api = {
  register: (email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),

  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  uploadQuestionnaire: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('/uploads/questionnaire', { method: 'POST', body: fd });
  },

  uploadReference: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('/uploads/reference', { method: 'POST', body: fd });
  },

  listQuestionnaires: () => request('/uploads/questionnaires'),
  listReferences: () => request('/uploads/references'),
  getQuestions: (qid) => request(`/uploads/questionnaire/${qid}/questions`),

  buildIndex: () => request('/index/build', { method: 'POST' }),

  generate: (questionnaire_id) =>
    request('/generate', { method: 'POST', body: JSON.stringify({ questionnaire_id }) }),

  regenerate: (question_id) =>
    request(`/regenerate/${question_id}`, { method: 'POST' }),

  editAnswer: (answer_id, answer_text, citations) =>
    request(`/answers/${answer_id}`, {
      method: 'PUT',
      body: JSON.stringify({ answer_text, citations }),
    }),

  listRuns: () => request('/runs'),
  getRun: (run_id) => request(`/runs/${run_id}`),

  exportRun: (run_id, format = 'xlsx') => request(`/export/${run_id}?format=${format}`),
};

export function setToken(token) {
  localStorage.setItem('token', token);
}

export function clearToken() {
  localStorage.removeItem('token');
}

export function isLoggedIn() {
  return !!getToken();
}
