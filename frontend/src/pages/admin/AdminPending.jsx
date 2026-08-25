import { useEffect, useState } from 'react';
import { Check, X, ArrowDownLeft, ArrowUpRight, ArrowLeftRight, Clock } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const typeMeta = {
  deposit: { label: 'Deposit', icon: ArrowDownLeft, tint: '#34D399', bg: 'rgba(52,211,153,0.15)' },
  withdrawal: { label: 'Withdrawal', icon: ArrowUpRight, tint: '#FB7185', bg: 'rgba(251,113,133,0.15)' },
  transfer: { label: 'Transfer', icon: ArrowLeftRight, tint: '#C4B5FD', bg: 'rgba(196,181,253,0.15)' },
};

export default function AdminPending() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actioningId, setActioningId] = useState(null);
  const [actionError, setActionError] = useState({});

  async function load() {
    try {
      const res = await api.get('/admin/transactions/pending');
      setPending(res.data);
    } catch {
      setError('Could not load pending transactions.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAction(id, action) {
    setActioningId(id);
    setActionError((prev) => ({ ...prev, [id]: '' }));
    try {
      await api.post(`/admin/transactions/${id}/${action}`);
      setPending((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      setActionError((prev) => ({
        ...prev,
        [id]: err.response?.data?.message || `Could not ${action} this transaction.`,
      }));
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Pending Approvals</h1>
        <p className="text-sm text-[var(--text-3)]">
          {pending.length} transaction{pending.length === 1 ? '' : 's'} waiting for review
        </p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {!loading && !error && (
        <div className="space-y-3">
          {pending.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              Nothing pending — you're all caught up.
            </div>
          )}

          {pending.map((tx) => {
            const meta = typeMeta[tx.transaction_type];
            const Icon = meta.icon;
            const isActing = actioningId === tx.id;

            return (
              <div key={tx.id} className="glass rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: meta.bg, color: meta.tint }}
                    >
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium">{meta.label}</p>
                        <span
                          className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide"
                          style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
                        >
                          <Clock size={10} /> Pending
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-3)] truncate">
                        {tx.sender_account_number || '—'} → {tx.receiver_account_number || '—'}
                      </p>
                      {tx.description && (
                        <p className="text-xs text-[var(--text-3)] truncate">{tx.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <p className="text-sm font-semibold font-mono">{formatMoney(tx.amount)}</p>
                    <p className="text-[11px] text-[var(--text-3)]">
                      {new Date(tx.timestamp).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>

                {actionError[tx.id] && (
                  <p className="text-xs text-[var(--danger)]">{actionError[tx.id]}</p>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleAction(tx.id, 'approve')}
                    disabled={isActing}
                    className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                    style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
                  >
                    <Check size={14} /> Approve
                  </button>
                  <button
                    onClick={() => handleAction(tx.id, 'reject')}
                    disabled={isActing}
                    className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                    style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}
                  >
                    <X size={14} /> Reject
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}