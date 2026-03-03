import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setToken } from '../api';

export default function AuthPage() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'register') {
        await api.register(email, password);
        // auto-login after register
      }
      const data = await api.login(email, password);
      setToken(data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '80px auto' }}>
      <h1>📋 Questionnaire Answering Tool</h1>
      <p className="mb-2" style={{ color: 'var(--muted)' }}>
        Upload questionnaires & references, generate grounded answers with citations.
      </p>
      <div className="card">
        <div className="flex mb-2">
          <button
            className={mode === 'login' ? '' : 'secondary'}
            onClick={() => setMode('login')}
          >
            Login
          </button>
          <button
            className={mode === 'register' ? '' : 'secondary'}
            onClick={() => setMode('register')}
          >
            Register
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Register'}
          </button>
        </form>
      </div>
    </div>
  );
}
