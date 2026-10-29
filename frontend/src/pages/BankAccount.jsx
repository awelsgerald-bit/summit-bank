import { useEffect, useState } from 'react';
import { Landmark, Copy, Check, Clock, ShieldAlert, Info, RefreshCw } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../utils/errors';

const PHONE_RE = /^(0\d{10}|\+234\d{10})$/;
const STALE_PENDING_MS = 2 * 60 * 1000;

function errorText(err, fallback) {
  return errorMessage(err, fallback);
}

function CopyButton({ value, label }) {
  const [state, setState] = useState('idle');

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setState('copied');
    } catch {
      setState('failed');
    }
    setTimeout(() => setState('idle'), 2000);
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy ${label}`}
      className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full glass"
    >
      {state === 'copied' ? <Check size={14} /> : <Copy size={14} />}
      {state === 'copied' ? 'Copied' : state === 'failed' ? 'Copy failed' : 'Copy'}
    </button>
  );
}

function Disclosure({ bankName }) {
  return (
    <div className="glass rounded-2xl p-4 flex gap-3">
      <Info size={18} className="shrink-0 mt-0.5 text-[var(--text-2)]" />
      <div className="text-xs text-[var(--text-2)] space-y-2">
        <p className="font-medium text-[var(--text-1)]">This is not a Summit Bank account</p>
        <p>
          This account number is provided by StroWallet through its banking partner
          {bankName ? ` (${bankName})` : ''}. Summit Bank does not hold your money in this account.
        </p>
        <p>
          Transfers to it are credited to your Summit balance only after Summit verifies the payment
          and approves it. Fees charged along the way may reduce the amount you receive.
        </p>
      </div>
    </div>
  );
}

export default function BankAccount() {
  const { user, refreshProfile } = useAuth();
  const [account, setAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  const [phoneInput, setPhoneInput] = useState(null);
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  useEffect(() => {
    let cancelled = false;
    api
      .get('/strowallet/my-account')
      .then((res) => {
        if (cancelled) return;
        setAccount(res.data);
        setLoadError('');
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err?.response?.status === 404) {
          setAccount(null);
          setLoadError('');
        } else {
          setLoadError(errorText(err, 'We could not load your bank account. Please try again.'));
        }
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  function reload() {
    setLoading(true);
    setReloadKey((k) => k + 1);
  }

  const phoneValue = phoneInput ?? user?.phone_number ?? '';

  async function apply(e) {
    e.preventDefault();
    setFormError('');
    const cleanPhone = phoneValue.replace(/[\s-]/g, '');
    if (!PHONE_RE.test(cleanPhone)) {
      setFormError('Enter a valid Nigerian phone number, e.g. 08012345678 or +2348012345678.');
      return;
    }
    if (!agreed) {
      setFormError('Please confirm that you understand this account is provided by StroWallet.');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/strowallet/apply', { phone: cleanPhone });
      try {
        await refreshProfile();
      } catch {
        // profile refresh is a convenience; the account itself was created
      }
      reload();
    } catch (err) {
      if (err?.response?.status === 409) {
        reload();
      } else {
        setFormError(errorText(err, 'We could not create your account right now. Please try again.'));
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-lg mx-auto">
        <div className="glass rounded-2xl p-6 text-sm text-[var(--text-2)]">Loading your bank account…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="max-w-lg mx-auto space-y-4">
        <div className="glass rounded-2xl p-6 space-y-4">
          <p className="text-sm text-[var(--text-2)]">{loadError}</p>
          <button type="button" onClick={reload} className="btn-primary rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2">
            <RefreshCw size={14} /> Try again
          </button>
        </div>
      </div>
    );
  }

  const isStalePending =
    account?.status === 'pending' &&
    account.created_at &&
    Date.now() - new Date(account.created_at).getTime() > STALE_PENDING_MS;

  const showForm = !account || account.status === 'failed';

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full flex items-center justify-center glass">
          <Landmark size={18} />
        </div>
        <div>
          <h1 className="font-display text-lg font-semibold">Bank Account</h1>
          <p className="text-xs text-[var(--text-2)]">Receive bank transfers into your Summit balance</p>
        </div>
      </div>

      {account?.mode === 'sandbox' && (
        <div className="rounded-2xl p-4 text-xs flex gap-3" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
          <ShieldAlert size={18} className="shrink-0" />
          <p>Test mode: this is a sandbox account. Real money sent to it will not arrive.</p>
        </div>
      )}

      {account?.status === 'active' && (
        <div className="glass rounded-2xl p-5 space-y-4">
          <div>
            <p className="text-xs text-[var(--text-3)]">Bank</p>
            <p className="font-display text-sm font-medium">{account.bank_name}</p>
          </div>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs text-[var(--text-3)]">Account number</p>
              <p className="font-mono text-xl tracking-wider">{account.nuban_account_number}</p>
            </div>
            <CopyButton value={account.nuban_account_number} label="account number" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-3)]">Account name</p>
            <p className="font-display text-sm font-medium">{account.account_name}</p>
          </div>
        </div>
      )}

      {account?.status === 'pending' && (
        <div className="glass rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium" style={{ color: '#FBBF24' }}>
            <Clock size={16} /> Setting up your account
          </div>
          <p className="text-xs text-[var(--text-2)]">
            {isStalePending
              ? 'This is taking longer than usual. Check again in a moment.'
              : 'Your account is being created. This usually takes a few seconds.'}
          </p>
          <button type="button" onClick={reload} className="glass rounded-xl px-4 py-2 text-xs font-medium flex items-center gap-2">
            <RefreshCw size={14} /> Check again
          </button>
        </div>
      )}

      {account?.status === 'suspended' && (
        <div className="glass rounded-2xl p-5 space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium" style={{ color: '#F87171' }}>
            <ShieldAlert size={16} /> Account unavailable
          </div>
          <p className="text-xs text-[var(--text-2)]">
            This bank account is currently unavailable. Please contact support.
          </p>
        </div>
      )}

      {showForm && (
        <form onSubmit={apply} className="glass rounded-2xl p-5 space-y-4">
          <p className="text-sm font-medium">
            {account?.status === 'failed' ? 'We could not create your account. Try again.' : 'Get a bank account number'}
          </p>
          <div>
            <label htmlFor="ba-phone" className="text-xs text-[var(--text-3)] block mb-1">Phone number</label>
            <input
              id="ba-phone"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              value={phoneValue}
              onChange={(e) => setPhoneInput(e.target.value)}
              placeholder="08012345678"
              className="input-field w-full rounded-xl px-4 py-3 text-sm bg-transparent outline-none"
            />
          </div>

          <Disclosure bankName={null} />

          <label className="flex items-start gap-2 text-xs text-[var(--text-2)]">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5"
            />
            <span>I understand this account is provided by StroWallet through its banking partner, not by Summit Bank.</span>
          </label>

          {formError && <p role="alert" className="text-xs" style={{ color: '#F87171' }}>{formError}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="btn-primary w-full rounded-xl py-3 text-sm font-medium"
          >
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>
      )}

      {account?.status === 'active' && <Disclosure bankName={account.bank_name} />}
    </div>
  );
}