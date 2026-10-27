import { useCallback, useEffect, useRef, useState } from 'react';
import { Lock } from 'lucide-react';
import { registerPinAsker } from '../api/client';

// Renders the PIN box and wires it to the API client. Mount once, near the top of the app.
export function PinPrompt() {
  const [request, setRequest] = useState(null); // { message, resolve }
  const [pin, setPin] = useState('');
  const inputRef = useRef(null);

  const ask = useCallback(
    (message) =>
      new Promise((resolve) => {
        setPin('');
        setRequest({ message, resolve });
      }),
    []
  );

  useEffect(() => {
    registerPinAsker(ask);
    return () => registerPinAsker(null);
  }, [ask]);

  useEffect(() => {
    if (request) inputRef.current?.focus();
  }, [request]);

  if (!request) return null;

  function finish(value) {
    request.resolve(value);
    setRequest(null);
    setPin('');
  }

  const valid = /^\d{4,6}$/.test(pin);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (valid) finish(pin);
        }}
        className="panel rounded-3xl w-full max-w-xs p-6 space-y-4 fade-in"
      >
        <div className="flex items-center gap-2">
          <Lock size={16} className="text-[var(--pink-accent)]" />
          <h3 className="font-display text-base font-medium">Transaction PIN</h3>
        </div>
        <p className="text-sm text-[var(--text-2)]">{request.message}</p>
        <input
          ref={inputRef}
          type="password"
          inputMode="numeric"
          autoComplete="off"
          maxLength={6}
          value={pin}
          onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
          className="input-field rounded-xl px-4 py-3 w-full text-center text-lg tracking-[0.5em] font-mono text-[var(--text-1)] bg-transparent outline-none"
          aria-label="Transaction PIN"
        />
        <div className="flex gap-2">
          <button type="button" onClick={() => finish(null)} className="flex-1 rounded-full py-2.5 text-sm border border-white/10 text-[var(--text-2)]">
            Cancel
          </button>
          <button disabled={!valid} className="btn-primary flex-1 rounded-full py-2.5 text-sm font-medium">
            Confirm
          </button>
        </div>
      </form>
    </div>
  );
}
