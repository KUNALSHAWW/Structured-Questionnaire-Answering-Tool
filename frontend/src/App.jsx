import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import { isLoggedIn, clearToken } from './api';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import QuestionnaireView from './pages/QuestionnaireView';

function Nav() {
  const navigate = useNavigate();
  if (!isLoggedIn()) return null;
  return (
    <div className="nav">
      <strong>📋 Questionnaire Tool</strong>
      <div>
        <Link to="/dashboard">Dashboard</Link>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            clearToken();
            navigate('/');
          }}
          style={{ marginLeft: 16 }}
        >
          Logout
        </a>
      </div>
    </div>
  );
}

function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <div className="container">
        <Routes>
          <Route path="/" element={isLoggedIn() ? <Navigate to="/dashboard" /> : <AuthPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/questionnaire/:runId"
            element={
              <ProtectedRoute>
                <QuestionnaireView />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
