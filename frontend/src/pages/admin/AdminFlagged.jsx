import { useEffect, useState } from 'react';
import { Check, X, AlertTriangle, ArrowDownLeft, ArrowUpRight, ArrowLeftRight } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const typeMeta = {
  deposit: { label: 'Deposit', icon: ArrowDownLeft },
  withdrawal: { label: 'Withdrawal', icon: ArrowUpRight },
  transfer: { label: 'Transfer', icon: ArrowLeftRight },
};

export default function AdminFlagged() {
  const [flagged, setFlagged] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);

  async function load() {
    try {
      const res = await api.get('/admin/transactions/flagged');
      setFlagged(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAction(id, action) {
    setActioningId(id);
    try {
      await api.post(`/admin/transactions/${id}/${action}`);
      setFlagged((prev) => prev.filter((t) => t.id !== id));
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Flagged Transactions</h1>
        <p className="text-sm text-[var(--text-3)]">{flagged.length} transaction{flagged.length === 1 ? '' : 's'} needing careful review</p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {flagged.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              Nothing flagged right now.
            </div>
          )}
          {flagged.map((tx) => {
            const meta = typeMeta[tx.transaction_type];
            const Icon = meta.icon;
            const isActing = actioningId === tx.id;
            const reasons = tx.flag_reasons ? tx.flag_reasons.split('; ') : [];

            return (
              <div
                key={tx.id}
                className="rounded-2xl p-4 space-y-3"
                style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.25)' }}
              >
                <div className="flex items-center justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                      style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
                    >
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{meta.label}</p>
                      <p className="text-xs text-[var(--text-3)] truncate">
                        {tx.sender_account_number || '—'} → {tx.receiver_account_number || '—'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-semibold font-mono">{formatMoney(tx.amount)}</p>
                    <p className="text-[11px] text-[var(--text-3)]">
                      {new Date(tx.timestamp).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </p>
                  </div>
                </div>

                <div className="rounded-xl p-3 space-y-1.5" style={{ background: 'rgba(0,0,0,0.15)' }}>
                  <div className="flex items-center gap-1.5 text-[#FBBF24]">
                    <AlertTriangle size={12} />
                    <span className="text-[10px] uppercase tracking-wide font-medium">Flag reasons</span>
                  </div>
                  {reasons.map((r, i) => (
                    <p key={i} className="text-xs text-[var(--text-2)] pl-4">
                      · {r}
                    </p>
                  ))}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleAction(tx.id, 'approve')}
                    disabled={isActing}
                    className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                    style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
                  >
                    <Check size={14} /> Approve Anyway
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