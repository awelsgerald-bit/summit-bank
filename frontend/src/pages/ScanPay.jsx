import { useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, ChevronLeft, Clock, CreditCard, ShieldCheck, Share2 } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import QrCamera from '../components/QrCamera';
import QrSwitch from '../components/QrSwitch';
import { errorMessage, formatDateTime, formatMoney } from '../utils/errors';

function newKey() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `k-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

function initials(name) {
  return (name || '?').split(/\s+/).map((p) => p[0]).slice(0, 2).join('').toUpperCase();
}

function Row({ label, children }) {
  return (
    <div className="flex items-start justify-between gap-4 py-3 text-sm">
      <span className="text-[var(--text-3)] shrink-0">{label}</span>
      <span className="text-right break-words min-w-0">{children}</span>
    </div>
  );
}

// Scan & Pay: scan -> check who you are paying and enter the amount -> confirm -> PIN -> receipt.
export default function ScanPay() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState('scan'); // scan | pay | confirm | done
  const [scanRound, setScanRound] = useState(0); // changing this restarts the camera
  const [target, setTarget] = useState(null); // what /qr/resolve returned, plus the scanned payload
  const [amount, setAmount] = useState('');
  const [narration, setNarration] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [copied, setCopied] = useState(false);
  const keyRef = useRef(null); // one key per payment attempt; a retry reuses it so money cannot move twice

  const fixed = target?.request?.amount || null;
  const value = Number(amount);
  const balance = Number(user?.balance ?? 0);
  const amountProblem = useMemo(() => {
    if (!amount) return '';
    if (!/^\d+(\.\d{0,2})?$/.test(amount)) return 'Use numbers only, with up to 2 decimals.';
    if (!(value > 0)) return 'Enter an amount greater than zero.';
    if (value > balance) return 'This is more than your available balance.';
    return '';
  }, [amount, value, balance]);
  const canContinue = amount && !amountProblem;

  async function handleScan(text, scanError) {
    if (scanError) return setError(scanError);
    setError('');
    setBusy(true);
    try {
      const res = await api.post('/qr/resolve', { payload: text });
      setTarget({ ...res.data, payload: text });
      setAmount(res.data.request?.amount ? String(Number(res.data.request.amount)) : '');
      setNarration(res.data.request?.note || res.data.request?.reference || '');
      setStep('pay');
    } catch (err) {
      setError(errorMessage(err, 'Could not read that QR code. Try again.'));
      setScanRound((n) => n + 1);
    } finally {
      setBusy(false);
    }
  }

  function goConfirm() {
    keyRef.current = newKey();
    setError('');
    setStep('confirm');
  }

  async function pay() {
    setError('');
    setBusy(true);
    try {
      const res = await api.post(
        '/qr/transfer',
        { payload: target.payload, amount: Number(amount).toFixed(2), narration: narration || undefined },
        { headers: { 'Idempotency-Key': keyRef.current } }
      );
      setReceipt(res.data);
      setStep('done');
      refreshProfile();
    } catch (err) {
      if (err.pinCancelled) setError('Payment cancelled. No money was taken.');
      else setError(errorMessage(err, 'The payment did not go through. You can try again; you will not be charged twice.'));
    } finally {
      setBusy(false);
    }
  }

  function again() {
    setStep('scan');
    setTarget(null);
    setAmount('');
    setNarration('');
    setReceipt(null);
    setError('');
    setScanRound((n) => n + 1);
  }

  async function shareReceipt() {
    const text = `Summit Bank receipt\n${formatMoney(receipt.amount)} to ${receipt.recipient.full_name}\nRef: ${receipt.reference}\n${formatDateTime(receipt.timestamp)}`;
    try {
      if (navigator.share) await navigator.share({ title: 'Summit Bank receipt', text });
      else {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch {
      /* the person closed the share sheet */
    }
  }

  const errorBox = error && (
    <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3" role="alert">
      {error}
    </div>
  );

  // ------------------------------------------------------------------ scan
  if (step === 'scan') {
    return (
      <div className="max-w-lg mx-auto space-y-6 fade-in">
        <QrSwitch active="scan" />
        <div className="text-center">
          <h1 className="font-display text-xl font-semibold">Scan to pay</h1>
          <p className="text-sm text-[var(--text-3)] mt-1">Point your camera at a Summit Bank QR code.</p>
        </div>
        <QrCamera key={scanRound} onScan={handleScan} />
        {busy && <p className="text-xs text-center text-[var(--text-3)]">Checking the code…</p>}
        {errorBox}
        <div className="card-dark rounded-3xl p-5 text-center" style={{ background: '#14101F', border: '1px solid rgba(255,255,255,0.08)' }}>
          <p className="font-display text-sm">Scan a QR code</p>
          <p className="text-xs mt-1" style={{ color: 'var(--text-3)' }}>
            Payments between Summit Bank accounts are instant and free. You will confirm the amount and your PIN next.
          </p>
        </div>
      </div>
    );
  }

  // ------------------------------------------------------------------ done
  if (step === 'done' && receipt) {
    const held = receipt.status === 'pending_review';
    return (
      <div className="max-w-lg mx-auto space-y-4 fade-in">
        <div className="text-center pt-2 pb-2">
          <div className="relative w-20 h-20 mx-auto mb-5">
            {!held && <span className="check-ring absolute inset-0 rounded-full" style={{ background: 'rgba(179,165,227,0.35)' }} />}
            <div className="check-pop relative w-20 h-20 rounded-full flex items-center justify-center grad-primary" style={held ? { background: 'rgba(251,191,36,0.2)', color: '#FBBF24' } : undefined}>
              {held ? (
                <Clock size={34} />
              ) : (
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path className="check-path" d="M5 12.5l4.5 4.5L19 7.5" />
                </svg>
              )}
            </div>
          </div>
          <h2 className="font-display text-xl font-semibold">{held ? 'Payment under review' : 'Payment successful'}</h2>
          <p className="text-sm text-[var(--text-3)] mt-1">
            {held ? 'No money has moved yet. It will be sent once an admin approves it.' : `${formatMoney(receipt.amount)} sent to ${receipt.recipient.full_name}`}
          </p>
        </div>

        <div className="glass rounded-3xl px-6 py-3 divide-y divide-white/5">
          <Row label="Amount"><span className="font-display font-semibold">{formatMoney(receipt.amount)}</span></Row>
          <Row label="To">{receipt.recipient.full_name}<br /><span className="font-mono text-xs text-[var(--text-3)]">{receipt.recipient.account_number} · {receipt.recipient.bank_name}</span></Row>
          <Row label="From">{receipt.sender.full_name}<br /><span className="font-mono text-xs text-[var(--text-3)]">{receipt.sender.account_number}</span></Row>
          {receipt.narration && <Row label="Narration">{receipt.narration}</Row>}
          <Row label="Reference"><span className="font-mono text-xs">{receipt.reference}</span></Row>
          <Row label="Date">{formatDateTime(receipt.timestamp)}</Row>
          <Row label="Status">{held ? 'Pending review' : 'Completed'}</Row>
        </div>

        <div className="flex gap-3">
          <button onClick={shareReceipt} className="ghost-btn flex-1 rounded-2xl py-3 text-xs flex items-center justify-center gap-2">
            {copied ? <Check size={14} /> : <Share2 size={14} />} {copied ? 'Copied' : 'Share receipt'}
          </button>
          <button onClick={again} className="ghost-btn flex-1 rounded-2xl py-3 text-xs">Pay someone else</button>
        </div>
        <button onClick={() => navigate('/dashboard')} className="btn-primary w-full rounded-full py-3 text-sm font-medium">Done</button>
      </div>
    );
  }

  // ------------------------------------------------------------------ pay and confirm
  const recipient = target.recipient;
  return (
    <div className="max-w-lg mx-auto space-y-5 fade-in">
      <div className="flex items-center gap-3">
        <button onClick={step === 'confirm' ? () => setStep('pay') : again} aria-label="Back" className="text-[var(--text-2)] w-9 h-9 flex items-center justify-center">
          <ChevronLeft size={20} />
        </button>
        <h1 className="font-display text-lg font-medium flex-1">{step === 'confirm' ? 'Confirm payment' : 'Pay with QR'}</h1>
      </div>

      <div>
        <p className="text-xs text-[var(--text-3)] mb-2">Source of funds</p>
        <div className="card-dark rounded-2xl p-4 flex items-center gap-4" style={{ background: '#14101F', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div className="w-12 h-9 rounded-lg grad-primary flex items-center justify-center shrink-0"><CreditCard size={18} /></div>
          <div className="min-w-0 flex-1">
            <p className="text-sm">Summit Account</p>
            <p className="font-mono text-xs" style={{ color: 'var(--text-3)' }}>{user?.account_number}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text-3)' }}>Available</p>
            <p className="font-display text-sm font-semibold">{formatMoney(balance)}</p>
          </div>
        </div>
      </div>

      <div>
        <p className="text-xs text-[var(--text-3)] mb-2">Pay to</p>
        <div className="glass rounded-2xl p-4 flex items-center gap-4">
          <div className="w-11 h-11 rounded-full grad-primary flex items-center justify-center text-sm font-semibold shrink-0">{initials(recipient.full_name)}</div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate">{recipient.full_name}</p>
            <p className="font-mono text-xs text-[var(--text-3)]">{recipient.account_number} · {recipient.bank_name}</p>
          </div>
          <span className="flex items-center gap-1 text-[10px] rounded-full px-2.5 py-1" style={{ background: 'rgba(52,211,153,0.14)', color: '#34D399' }}>
            <ShieldCheck size={12} /> Verified
          </span>
        </div>
      </div>

      {step === 'pay' ? (
        <>
          <div>
            <label htmlFor="qr-amount" className="text-xs text-[var(--text-3)] mb-2 block">
              {fixed ? 'Amount requested' : 'Amount'}
            </label>
            <div className="input-field amount-glow rounded-2xl px-5 py-4 flex items-center gap-2">
              <span className="text-[var(--text-3)] font-display text-sm">NGN</span>
              <input
                id="qr-amount"
                inputMode="decimal"
                autoFocus={!fixed}
                readOnly={!!fixed}
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ''))}
                placeholder="0.00"
                className="bg-transparent w-full font-display text-2xl font-semibold outline-none placeholder:text-[var(--text-3)]"
              />
            </div>
            {amountProblem && <p className="text-xs text-[var(--danger)] mt-2" role="alert">{amountProblem}</p>}
            {target.request?.reference && <p className="text-xs text-[var(--text-3)] mt-2">Reference: {target.request.reference}</p>}
          </div>

          <div>
            <label htmlFor="qr-narration" className="text-xs text-[var(--text-3)] mb-2 block">Narration (optional)</label>
            <div className="input-field rounded-xl px-4 py-3">
              <input
                id="qr-narration"
                maxLength={140}
                value={narration}
                onChange={(e) => setNarration(e.target.value)}
                placeholder="What's this for?"
                className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
              />
            </div>
          </div>
          {errorBox}
          <button onClick={goConfirm} disabled={!canContinue} className="btn-primary w-full rounded-full py-3.5 text-sm font-medium">
            Continue
          </button>
        </>
      ) : (
        <>
          <div className="glass rounded-3xl px-6 py-3 divide-y divide-white/5">
            <Row label="You send"><span className="font-display text-lg font-semibold">{formatMoney(value)}</span></Row>
            <Row label="Fee">Free</Row>
            {narration && <Row label="Narration">{narration}</Row>}
            <Row label="Balance after">{formatMoney(balance - value)}</Row>
          </div>
          <p className="text-xs text-[var(--text-3)] text-center">Check the name above. Payments cannot be undone. You will be asked for your PIN.</p>
          {errorBox}
          <button onClick={pay} disabled={busy} className="btn-primary w-full rounded-full py-3.5 text-sm font-medium">
            {busy ? 'Sending…' : `Pay ${formatMoney(value)}`}
          </button>
        </>
      )}
      <p className="text-center text-xs"><Link to="/receive" className="text-[var(--pink-accent)]">Show my QR code instead</Link></p>
    </div>
  );
}
