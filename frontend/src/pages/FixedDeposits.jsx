import { useEffect, useState } from 'react';
import { PiggyBank, Lock, CheckCircle2 } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function daysRemaining(maturesAt) {
  const diff = new Date(maturesAt) - new Date();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

export default function FixedDeposits() {
  const { user, refreshProfile } = useAuth();
  const [deposits, setDeposits] = useState([]);
  const [terms, setTerms] = useState({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const [amount, setAmount] = useState('');
  const [termDays, setTermDays] = useState('30');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    try {
      const [depositsRes, termsRes] = await Promise.all([
        api.get('/fixed-deposits'),
        api.get('/fixed-deposits/terms'),
      ]);
      setDeposits(depositsRes.data);
      setTerms(termsRes.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    refreshProfile(); // opportunistically sweeps any matured deposits on page load too
  }, []);

  async function handleOpen(e) {
    e.preventDefault();
    setError('');
    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/fixed-deposits', {
        principal_amount: numericAmount,
        term_days: parseInt(termDays, 10),
      });
      setDeposits((prev) => [res.data, ...prev]);
      setAmount('');
      setShowForm(false);
      await refreshProfile();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not open fixed deposit.');
    } finally {
      setSubmitting(false);
    }
  }

  const selectedRate = terms[termDays];
  const projectedPayout = amount && selectedRate ? parseFloat(amount) * (1 + selectedRate / 100) : null;

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-semibold mb-1">Fixed Deposits</h1>
          <p className="text-sm text-[var(--text-3)]">Lock funds and earn a fixed return.</p>
        </div>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5"
        >
          <PiggyBank size={14} /> {showForm ? 'Cancel' : 'Open New'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleOpen} className="glass rounded-2xl p-4 space-y-3">
          {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Amount to lock</label>
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
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(terms).map(([days, rate]) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => setTermDays(days)}
                  className={`rounded-xl py-2 text-xs text-center transition ${
                    termDays === days ? 'toggle-active' : 'toggle-pill text-[var(--text-2)]'
                  }`}
                >
                  <div className="font-medium">{days}d</div>
                  <div className="opacity-70">{rate}%</div>
                </button>
              ))}
            </div>
          </div>
          {projectedPayout && (
            <p className="text-xs text-[var(--text-3)]">
              Matures to <span className="font-mono text-[var(--text-1)]">{formatMoney(projectedPayout)}</span>
            </p>
          )}
          <p className="text-[11px] text-[var(--text-3)]">
            Available balance: <span className="font-mono">{formatMoney(user?.balance ?? 0)}</span>
          </p>
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary w-full rounded-full py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {submitting ? 'Opening...' : 'Lock Funds'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {deposits.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
              No fixed deposits yet.
            </div>
          )}
          {deposits.map((fd) => {
            const isMatured = fd.status === 'matured';
            const remaining = daysRemaining(fd.matures_at);
            return (
              <div key={fd.id} className="glass rounded-2xl p-4 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{
                      background: isMatured ? 'rgba(52,211,153,0.15)' : 'rgba(196,181,253,0.15)',
                      color: isMatured ? '#34D399' : '#C4B5FD',
                    }}
                  >
                    {isMatured ? <CheckCircle2 size={18} /> : <Lock size={18} />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{formatMoney(fd.principal_amount)}</p>
                    <p className="text-xs text-[var(--text-3)]">
                      {isMatured ? 'Matured & credited' : `${remaining} day${remaining === 1 ? '' : 's'} remaining`}
                    </p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-semibold font-mono">{formatMoney(fd.payout_amount)}</p>
                  <p className="text-[11px] text-[var(--text-3)]">{fd.interest_rate}% · {fd.term_days}d</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}