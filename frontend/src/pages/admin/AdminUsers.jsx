import { useEffect, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api
      .get('/admin/users')
      .then((res) => setUsers(res.data))
      .catch(() => setError('Could not load users.'))
      .finally(() => setLoading(false));
  }, []);

  const visible = useMemo(() => {
    if (!search.trim()) return users;
    const q = search.trim().toLowerCase();
    return users.filter(
      (u) =>
        u.full_name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.account_number.includes(q)
    );
  }, [users, search]);

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Users</h1>
        <p className="text-sm text-[var(--text-3)]">{users.length} registered accounts</p>
      </div>

      <div className="input-field rounded-full px-4 py-2.5 flex items-center gap-2 max-w-xs">
        <Search size={16} className="text-[var(--text-3)]" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search name, email, account number"
          className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
        />
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading users...</p>}
      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {!loading && !error && (
        <div className="space-y-3">
          {visible.map((u) => (
            <div key={u.id} className="glass rounded-2xl p-4 flex items-center justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium">{u.full_name}</p>
                  {u.role === 'admin' && (
                    <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full toggle-active">
                      Admin
                    </span>
                  )}
                </div>
                <p className="text-xs text-[var(--text-3)]">{u.email}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-mono">{u.account_number}</p>
                <p className="text-xs text-[var(--text-3)]">
                  Joined {new Date(u.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-sm font-semibold font-mono">{formatMoney(u.balance)}</p>
              </div>
            </div>
          ))}
          {visible.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No users match this search.
            </div>
          )}
        </div>
      )}
    </div>
  );
}