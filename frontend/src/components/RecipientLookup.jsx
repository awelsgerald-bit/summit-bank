import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import api from '../api/client';
import { errorMessage } from '../utils/errors';

// Shows who owns an account number as soon as a full number is typed.
// onResult receives { name, is_self } when found, or null otherwise, so a form can react.
export default function RecipientLookup({ accountNumber, onResult }) {
  const [state, setState] = useState({ status: 'idle' });
  const account = (accountNumber || '').trim();

  useEffect(() => {
    if (!/^\d{10}$/.test(account)) {
      setState({ status: 'idle' });
      onResult?.(null);
      return undefined;
    }
    let cancelled = false;
    setState({ status: 'loading' });
    const timer = setTimeout(async () => {
      try {
        const res = await api.get(`/account/lookup/${account}`);
        if (cancelled) return;
        setState({ status: 'found', ...res.data });
        onResult?.(res.data);
      } catch (err) {
        if (cancelled) return;
        const notFound = err.response?.status === 404;
        setState({ status: notFound ? 'missing' : 'error', message: errorMessage(err, 'Could not check this account.') });
        onResult?.(notFound ? { not_found: true } : null);
      }
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // onResult is intentionally left out: parents pass a new function every render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [account]);

  if (state.status === 'idle') return null;
  if (state.status === 'loading') return <p className="text-xs text-[var(--text-3)]">Checking account...</p>;
  if (state.status === 'found') {
    return state.is_self ? (
      <p className="text-xs flex items-center gap-1.5 text-[var(--danger)]">
        <XCircle size={14} /> That is your own account.
      </p>
    ) : (
      <p className="text-xs flex items-center gap-1.5 text-[var(--success)]">
        <CheckCircle2 size={14} /> {state.name}
      </p>
    );
  }
  return (
    <p className="text-xs flex items-center gap-1.5 text-[var(--danger)]">
      <XCircle size={14} /> {state.status === 'missing' ? 'No Summit Bank account has this number.' : state.message}
    </p>
  );
}
