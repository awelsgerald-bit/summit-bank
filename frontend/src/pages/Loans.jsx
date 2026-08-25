import { useEffect, useState } from 'react';
import { HandCoins, Clock, CheckCircle2, XCircle, Banknote } from 'lucide-react';
import api from '../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const statusMeta = {
  pending: { label: 'Pending Review', icon: Clock, tint: '#FBBF24', bg: 'rgba(251,191,36,0.15)' },
  approved: { label: 'Active', icon: Banknote, tint: '#34D399', bg: 'rgba(52,211,153,0.15)' },
  rejected: { label: 'Rejected', icon: XCircle, tint: '#FB7185', bg: 'rgba(251,113,133,0.15)' },
  repaid: { label: 'Repaid', icon: CheckCircle2, tint: '#C4B5FD', bg: 'rgba(196,181,253,0.15)' },
};

export default function Loans() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [amount, setAmount] = useState('');
  const [term, setTerm] = useState('12');
  const [purpose, setPurpose] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [repayAmounts, setRepayAmounts] = useState({});
  const [repayingId, setRepayingId] = useState(null);
  const [repayError, setRepayError] = useState({});

  async function load() {
    try {
      const res = await api.get('/loans');
      setLoans(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleApply(e) {
    e.preventDefault();
    setError('');
    const numericAmount = parseFloat(amount);
    const numericTerm = parseInt(term, 10);
    if (!numericAmount || numericAmount <= 0) {
      setError('Enter a loan amount greater than zero.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/loans/apply', {
        principal_amount: numericAmount,
        term_months: numericTerm,
        purpose: purpose || undefined,
      });
      setLoans((prev) => [res.data, ...prev]);
      setAmount('');
      setPurpose('');
      setShowForm(false);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit loan application.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRepay(loanId) {
    const value = parseFloat(repayAmounts[loanId]);
    if (!value || value <= 0) {
      setRepayError((prev) => ({ ...prev, [loanId]: 'Enter an amount greater than zero.' }));
      return;
    }
    setRepayingId(loanId);
    setRepayError((prev) => ({ ...prev, [loanId]: '' }));
    try {
      const res = await api.post(`/loans/${loanId}/repay`, { amount: value });
      setLoans((prev) => prev.map((l) => (l.id === loanId ? res.data : l)));
      setRepayAmounts((prev) => ({ ...prev, [loanId]: '' }));
    } catch (err) {
      setRepayError((prev) => ({
        ...prev,
        [loanId]: err.response?.data?.message || 'Repayment failed.',
      }));
    } finally {
      setRepayingId(null);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold mb-1">Loans</h1>
          <p className="text-sm text-[var(--text-3)]">Apply for a loan or manage repayments.</p>
        </div>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5"
        >
          <HandCoins size={14} /> {showForm ? 'Cancel' : 'Apply'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleApply} className="glass rounded-2xl p-4 space-y-3">
          {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Amount</label>
            <div className="input-field rounded-xl px-4 py-2.5 flex items-center gap-1">
              <span className="text-[var(--text-3)] text-sm">$</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Term</label>
            <select
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              className="input-field rounded-xl px-4 py-2.5 w-full text-sm bg-transparent outline-none"
              style={{ colorScheme: 'dark' }}
            >
              {[3, 6, 12, 24, 36].map((m) => (
                <option key={m} value={m} className="bg-[#17122A]">
                  {m} months
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Purpose (optional)</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <input
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="What's this for?"
                className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
              />
            </div>
          </div>
          <p className="text-[11px] text-[var(--text-3)]">Flat 10% interest applies over the full term.</p>
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary w-full rounded-full py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {submitting ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {loans.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
              No loans yet.
            </div>
          )}
          {loans.map((loan) => {
            const meta = statusMeta[loan.status];
            const Icon = meta.icon;
            return (
              <div key={loan.id} className="glass rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: meta.bg, color: meta.tint }}
                    >
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{formatMoney(loan.principal_amount)}</p>
                        <span
                          className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide"
                          style={{ background: meta.bg, color: meta.tint }}
                        >
                          {meta.label}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-3)] truncate">
                        {loan.term_months} months · {loan.purpose || 'No purpose given'}
                      </p>
                    </div>
                  </div>
                </div>

                {loan.status === 'approved' && (
                  <div className="border-t border-white/5 pt-3 space-y-2">
                    <p className="text-xs text-[var(--text-3)]">
                      Outstanding: <span className="font-mono text-[var(--text-1)]">{formatMoney(loan.outstanding_balance)}</span>{' '}
                      of {formatMoney(loan.total_repayable)}
                    </p>
                    {repayError[loan.id] && (
                      <p className="text-xs text-[var(--danger)]">{repayError[loan.id]}</p>
                    )}
                    <div className="flex gap-2">
                      <div className="input-field rounded-full px-3 py-1.5 flex items-center gap-1 flex-1">
                        <span className="text-[var(--text-3)] text-xs">$</span>
                        <input
                          type="number"
                          step="0.01"
                          value={repayAmounts[loan.id] || ''}
                          onChange={(e) => setRepayAmounts((prev) => ({ ...prev, [loan.id]: e.target.value }))}
                          placeholder="Repay amount"
                          className="bg-transparent w-full text-xs outline-none placeholder:text-[var(--text-3)]"
                        />
                      </div>
                      <button
                        onClick={() => handleRepay(loan.id)}
                        disabled={repayingId === loan.id}
                        className="btn-primary rounded-full px-4 text-xs font-medium disabled:opacity-60"
                      >
                        Pay
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}