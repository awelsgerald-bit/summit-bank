import { createContext, useCallback, useContext, useState } from 'react';
import { ArrowDownLeft } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((title, message) => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, title, message, show: false }]);

    // trigger enter animation on next frame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setToasts((t) => t.map((x) => (x.id === id ? { ...x, show: true } : x)));
      });
    });

    setTimeout(() => {
      setToasts((t) => t.map((x) => (x.id === id ? { ...x, show: false } : x)));
      setTimeout(() => {
        setToasts((t) => t.filter((x) => x.id !== id));
      }, 400);
    }, 3600);
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-5 left-0 right-0 flex flex-col items-center gap-2.5 z-[60] px-4 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`toast-item glass rounded-2xl px-4 py-3 flex items-center gap-3 shadow-2xl pointer-events-auto ${t.show ? 'show' : ''}`}
          >
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
            >
              <ArrowDownLeft size={18} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium">{t.title}</p>
              <p className="text-xs text-[var(--text-3)] truncate">{t.message}</p>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}