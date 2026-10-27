import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Coins, Lock, Plus } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { errorMessage, formatMoney } from '../utils/errors';

export default function Save4Me() {
  const { user, refreshProfile } = useAuth();
  const [pots, setPots] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [target, setTarget] = useState('');
  const [creating, setCreating] = useState(false);

  // which pot has its amount box open, and for what: { id, kind: 'deposit' | 'withdraw' | 'close' }
  const [action, setAction] = useState(null);
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const res = await api.get('/savings/pots');
      setPots(res.data.pots);
      setTotal(Number(res.data.total_saved));
    } catch (err) {
      setError(errorMessage(err, 'Could not load your savings.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createPot(e) {
    e.preventDefault();
    setError('');
    setNotice('');
    setCreating(true);
    try {
      await api.post('/savings/pots', {
        name: name.trim(),
        target_amount: target ? parseFloat(target) : undefined,
      });
      setName('');
      setTarget('');
      setShowForm(false);
      await load();
    } catch (err) {
      setError(errorMessage(err, 'Could not create the pot.'));
    } finally {
      setCreating(false);
    }
  }

  async function runAction(e) {
    e.preventDefault();
    if (!action) return;
    setError('');
    setNotice('');
    setBusy(true);
    try {
      if (action.kind === 'close') {
        await api.post(`/savings/pots/${action.id}/close`);
        setNotice('Pot closed. The money is back in your wallet.');
      } else {
        await api.post(`/savings/pots/${action.id}/${action.kind}`, { amount: parseFloat(amount) });
        setNotice(action.kind === 'deposit' ? 'Money saved.' : 'Money moved back to your wallet.');
      }
      setAction(null);
      setAmount('');
      await Promise.all([load(), refreshProfile()]);
    } catch (err) {
      setError(errorMessage(err, 'That did not work. Nothing was moved.'));
    } finally {
      setBusy(false);
    }
  }

  const wallet = Number(user?.balance ?? 0);

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-medium">Save4Me</h2>
          <p className="text-sm text-[var(--text-3)]">
            Set money aside in pots. It stays yours, but it can't be spent or sent until you move it back. Pots do not earn interest.
          </p>
        </div>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5 shrink-0"
        >
          <Plus size={14} /> {showForm ? 'Close' : 'New pot'}
        </button>
      </div>

      <div className="glass rounded-2xl p-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-[var(--text-3)]">In your wallet</p>
          <p className="font-mono font-semibold">{formatMoney(wallet)}</p>
        </div>
        <div>
          <p className="text-[11px] uppercase tracking-wide text-[var(--text-3)]">Saved in pots</p>
          <p className="font-mono font-semibold">{formatMoney(total)}</p>
        </div>
      </div>

      {!user?.has_pin && (
        <Link
          to="/settings"
          className="flex items-center gap-2 text-sm rounded-xl px-4 py-3 border border-[rgba(251,191,36,0.3)] bg-[rgba(251,191,36,0.1)] text-[#FBBF24]"
        >
          <Lock size={15} /> Set a transaction PIN in Settings to start saving.
        </Link>
      )}

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </div>
      )}
      {notice && (
        <div className="text-sm text-[var(--success)] bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.25)] rounded-xl px-4 py-3">
          {notice}
        </div>
      )}

      {showForm && (
        <form onSubmit={createPot} className="glass rounded-3xl p-5 space-y-3">
          <label className="block text-xs text-[var(--text-3)]">
            Pot name (for example "School fees")
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={60}
              required
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <label className="block text-xs text-[var(--text-3)]">
            Goal amount in ₦ (optional)
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm font-mono text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <button disabled={creating} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
            {creating ? 'Creating...' : 'Create pot'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
      {!loading && pots.length === 0 && !showForm && (
        <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
          <Coins className="mx-auto mb-2" size={22} />
          No pots yet. Tap New pot to start.
        </div>
      )}

      <div className="space-y-3">
        {pots.map((pot) => {
          const balance = Number(pot.balance);
          const goal = pot.target_amount ? Number(pot.target_amount) : null;
          const percent = goal ? Math.min(100, Math.round((balance / goal) * 100)) : null;
          const open = action?.id === pot.id;
          return (
            <div key={pot.id} className="glass rounded-2xl p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{pot.name}</p>
                  {goal && (
                    <p className="text-xs text-[var(--text-3)]">
                      Goal {formatMoney(goal)} · {percent}%
                    </p>
                  )}
                </div>
                <p className="font-mono text-sm font-semibold shrink-0">{formatMoney(balance)}</p>
              </div>

              {goal && (
                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full grad-primary" style={{ width: `${percent}%` }} />
                </div>
              )}

              {open ? (
                <form onSubmit={runAction} className="space-y-2">
                  {action.kind === 'close' ? (
                    <p className="text-sm text-[var(--text-2)]">
                      Close this pot and move {formatMoney(balance)} back to your wallet?
                    </p>
                  ) : (
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      autoFocus
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder={action.kind === 'deposit' ? 'Amount to save (₦)' : 'Amount to take out (₦)'}
                      className="input-field rounded-xl px-4 py-3 w-full text-sm font-mono text-[var(--text-1)] bg-transparent outline-none"
                    />
                  )}
                  <div className="flex gap-2">
                    <button disabled={busy} className="btn-primary flex-1 rounded-full py-2 text-xs font-medium">
                      {busy ? 'Working...' : 'Confirm'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setAction(null)}
                      disabled={busy}
                      className="flex-1 rounded-full py-2 text-xs border border-white/10 text-[var(--text-2)]"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => { setAction({ id: pot.id, kind: 'deposit' }); setAmount(''); }}
                    className="btn-primary flex-1 rounded-full py-2 text-xs font-medium"
                  >
                    Add money
                  </button>
                  <button
                    onClick={() => { setAction({ id: pot.id, kind: 'withdraw' }); setAmount(''); }}
                    disabled={balance <= 0}
                    className="flex-1 rounded-full py-2 text-xs border border-white/10 text-[var(--text-1)] disabled:opacity-40"
                  >
                    Take out
                  </button>
                  <button
                    onClick={() => setAction({ id: pot.id, kind: 'close' })}
                    className="rounded-full px-4 py-2 text-xs border border-white/10 text-[var(--danger)]"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
