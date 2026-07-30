import { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import TransactionRow from '../components/TransactionRow';

const FILTERS = ['all', 'deposit', 'withdrawal', 'transfer'];

export default function History() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [sort, setSort] = useState('newest');

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await api.get('/transactions/history');
        if (!cancelled) setTransactions(res.data);
      } catch {
        if (!cancelled) setError('Could not load transaction history.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const visible = useMemo(() => {
    let list = [...transactions];

    if (filter !== 'all') {
      list = list.filter((t) => t.transaction_type === filter);
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter((t) => (t.description || '').toLowerCase().includes(q));
    }

    list.sort((a, b) => {
      const diff = new Date(a.timestamp) - new Date(b.timestamp);
      return sort === 'newest' ? -diff : diff;
    });

    return list;
  }, [transactions, filter, search, sort]);

  return (
    <div className="space-y-6 stagger">
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="input-field rounded-full px-4 py-2.5 flex items-center gap-2 flex-1 sm:max-w-xs">
          <Search size={16} className="text-[var(--text-3)]" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by description"
            className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-full text-xs capitalize toggle-pill ${
                filter === f ? 'toggle-active' : 'text-[var(--text-2)]'
              }`}
            >
              {f}
            </button>
          ))}

          <button
            onClick={() => setSort((s) => (s === 'newest' ? 'oldest' : 'newest'))}
            className="px-3 py-1.5 rounded-full text-xs toggle-pill text-[var(--text-2)]"
          >
            {sort === 'newest' ? 'Newest first' : 'Oldest first'}
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading transactions...</p>}

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="space-y-3">
          {visible.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No transactions match this filter.
            </div>
          )}
          {visible.map((tx) => (
            <TransactionRow key={tx.id} tx={tx} currentUserId={user.id} />
          ))}
        </div>
      )}
    </div>
  );
}