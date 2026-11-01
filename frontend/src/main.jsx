import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';
import { ToastProvider } from './context/ToastContext.jsx';
import { ThemeProvider } from './context/ThemeContext.jsx';
import { PinPrompt } from './context/PinContext.jsx';
import App from './App.jsx';
import './index.css';

// The free server sleeps when idle and takes a while to wake. Poke it now, while the page is
// still loading, so it is awake by the time someone taps Sign in.
try {
  if (import.meta.env.VITE_API_URL) fetch(`${import.meta.env.VITE_API_URL}/health`, { mode: 'no-cors', keepalive: true }).catch(() => {});
} catch {
  // best effort only
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <App />
            <PinPrompt />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);