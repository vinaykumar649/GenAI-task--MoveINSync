import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import ManageRoute from './pages/ManageRoute';
import BusDashboard from './pages/BusDashboard';
import Movi from './components/Movi';
import './App.css';

function AppContent() {
  const location = useLocation();
  const [chatbotOpen, setChatbotOpen] = useState(false);
  
  return (
    <div className="App">
      <nav className="navbar">
        <div className="navbar-content">
          <div className="navbar-brand">
            <h1 className="navbar-title">MoveInSync</h1>
            <p className="navbar-subtitle">Operations Hub</p>
          </div>
          <div className="navbar-links">
            <Link 
              to="/manage-route" 
              className={`nav-link ${location.pathname === '/manage-route' ? 'active' : ''}`}
            >
              <span className="nav-icon">🗺️</span>
              Routes
            </Link>
            <Link 
              to="/bus-dashboard" 
              className={`nav-link ${location.pathname === '/bus-dashboard' ? 'active' : ''}`}
            >
              <span className="nav-icon">🚌</span>
              Dashboard
            </Link>
          </div>
        </div>
      </nav>
      
      <div className="main-container">
        <Routes>
          <Route path="/" element={<ManageRoute />} />
          <Route path="/manage-route" element={<ManageRoute />} />
          <Route path="/bus-dashboard" element={<BusDashboard />} />
        </Routes>
      </div>
      
      <button 
        className={`chatbot-fab ${chatbotOpen ? 'open' : ''}`}
        onClick={() => setChatbotOpen(!chatbotOpen)}
        title="Open Movi Chat"
      >
        <span className="chatbot-icon">💬</span>
      </button>
      
      <div className={`chatbot-modal-overlay ${chatbotOpen ? 'visible' : 'hidden'}`} onClick={() => setChatbotOpen(false)}>
        <div className="chatbot-modal" onClick={(e) => e.stopPropagation()}>
          <div className="chatbot-header">
            <h3>Movi Assistant</h3>
            <button 
              className="close-btn"
              onClick={() => setChatbotOpen(false)}
            >
              ✕
            </button>
          </div>
          <Movi context={location.pathname} />
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
