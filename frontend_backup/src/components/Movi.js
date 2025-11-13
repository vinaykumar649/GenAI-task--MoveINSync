import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { ENDPOINTS } from '../config';
import './Movi.css';

const Movi = ({ context }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const recognitionRef = useRef(null);
  const sessionIdRef = useRef('');
  const messagesEndRef = useRef(null);

  const STORAGE_KEY = 'movi_chat_history';

  if (!sessionIdRef.current) {
    sessionIdRef.current = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  useEffect(() => {
    const savedMessages = localStorage.getItem(STORAGE_KEY);
    if (savedMessages) {
      try {
        setMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error('Failed to load chat history:', e);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const speakText = async (text) => {
    try {
      await axios.post(ENDPOINTS.TEXT_TO_SPEECH, { text });
    } catch (error) {
      console.error('Text-to-speech error:', error);
    }
  };

  const sendMessage = async (messageText = null, imageData = null) => {
    const textToSend = (messageText ?? input).trim();
    if (!textToSend && !imageData) {
      return;
    }
    
    const displayText = textToSend || (imageData ? 'Image shared' : '');
    const userEntry = {
      role: 'user',
      text: imageData ? `${displayText} 📷` : displayText,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userEntry]);
    setInput('');
    setAwaitingConfirmation(false);
    setLoading(true);

    try {
      const payload = {
        message: textToSend,
        context,
        sessionId: sessionIdRef.current
      };
      if (imageData) {
        payload.image = imageData;
      }
      
      const response = await axios.post(ENDPOINTS.CHAT, payload);
      if (response.data.sessionId) {
        sessionIdRef.current = response.data.sessionId;
      }
      
      const assistantText = response.data.response || "I'm not sure how to help with that.";
      const assistantEntry = {
        role: 'assistant',
        text: assistantText,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, assistantEntry]);
      setAwaitingConfirmation(Boolean(response.data.awaitingConfirmation));
      
      if (assistantText) {
        speakText(assistantText);
      }
    } catch (error) {
      const errorEntry = {
        role: 'assistant',
        text: 'Error communicating with Movi. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorEntry]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleMoviMessage = (event) => {
      if (event.detail?.message) {
        sendMessage(event.detail.message);
      }
    };
    window.addEventListener('moviMessage', handleMoviMessage);
    return () => window.removeEventListener('moviMessage', handleMoviMessage);
  }, []);

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition not supported in your browser');
      return;
    }
    
    if (!recognitionRef.current) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = event => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        setInput('');
        sendMessage(transcript);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
    
    setIsListening(true);
    recognitionRef.current.start();
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = e => {
      const imageData = e.target.result;
      sendMessage('What should I do with this trip?', imageData);
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const clearHistory = () => {
    if (window.confirm('Are you sure you want to clear chat history?')) {
      setMessages([]);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const contextDisplay = context === '/manage-route' ? '🗺️ Routes' :
                        context === '/bus-dashboard' ? '🚌 Operations' : '💼 General';

  return (
    <div className="movi-container">
      <div className="movi-messages">
        {messages.length === 0 && (
          <div className="movi-welcome">
            <div className="welcome-icon">💬</div>
            <h3>Welcome to Movi</h3>
            <p>Your AI Operations Assistant</p>
            <ul className="welcome-tips">
              <li>Ask about vehicles & drivers</li>
              <li>Check route & trip status</li>
              <li>Deploy vehicles to routes</li>
              <li>Manage stops and paths</li>
            </ul>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`movi-message ${msg.role}`}>
            <div className={`message-bubble ${msg.isError ? 'error' : ''}`}>
              {msg.text}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="movi-message assistant">
            <div className="message-bubble loading">
              <span className="loading-dot"></span>
              <span className="loading-dot"></span>
              <span className="loading-dot"></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="movi-input-section">
        {awaitingConfirmation && (
          <div className="confirmation-banner">
            ⚠️ Awaiting your confirmation to proceed. Reply with yes or no.
          </div>
        )}

        <div className="movi-input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
            placeholder="Type your message..."
            className="movi-input"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            className="send-btn"
            disabled={loading || !input.trim()}
            title="Send message"
          >
            ➤
          </button>
        </div>

        <div className="movi-actions">
          <button
            onClick={startListening}
            disabled={isListening || loading}
            className={`action-btn voice-btn ${isListening ? 'listening' : ''}`}
            title="Voice input"
          >
            {isListening ? '🎤' : '🎙️'}
          </button>

          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            ref={fileInputRef}
            style={{ display: 'none' }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="action-btn image-btn"
            disabled={loading}
            title="Upload image"
          >
            📷
          </button>

          <button
            onClick={clearHistory}
            className="action-btn clear-btn"
            title="Clear history"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  );
};

export default Movi;
