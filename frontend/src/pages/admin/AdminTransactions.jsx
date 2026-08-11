import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDownLeft, ArrowUpRight, ArrowLeftRight } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const typeMeta = {
  deposit: { label: 'Deposit', icon: ArrowDownLeft, tint: '#34D399', bg: 'rgba(52,211,153,0.15)' },
  withdrawal: { label: 'Withdrawal', icon: ArrowUpRight, tint: '#FB7185', bg: 'rgba(251,113,133,0.15)' },
  transfer: { label: 'Transfer', icon: ArrowLeftRight, tint: '#C4B5FD', bg: 'rgba(196,181,253,0.15)' },
};

export default function AdminTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/admin/transactions')
      .then((res) => setTransactions(res.data))
      .catch(() => setError('Could not load transactions.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Transactions</h1>
        <p className="text-sm text-[var(--text-3)]">Most recent {transactions.length} across all accounts</p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading transactions...</p>}
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {!loading && !error && (
        <div className="space-y-3">
          {transactions.map((tx) => {
            const meta = typeMeta[tx.transaction_type];
            const Icon = meta.icon;
            return (
              <Link
                key={tx.id}
                to={`/admin/transactions/${tx.id}`}
                className="hover-lift glass rounded-2xl p-4 flex items-center justify-between gap-4 flex-wrap"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: meta.bg, color: meta.tint }}
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
              </Link>
            );
          })}
          {transactions.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No transactions yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}