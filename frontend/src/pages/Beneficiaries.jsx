import { useEffect, useState } from 'react';
import { Trash2, UserPlus } from 'lucide-react';
import api from '../api/client';

export default function Beneficiaries() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [nickname, setNickname] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  async function load() {
    try {
      const res = await api.get('/beneficiaries');
      setList(res.data);
    } catch {
      setError('Could not load beneficiaries.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    setError('');
    if (!nickname.trim() || !accountNumber.trim()) {
      setError('Enter both a nickname and account number.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/beneficiaries', {
        nickname: nickname.trim(),
        account_number: accountNumber.trim(),
      });
      setList((prev) => [res.data, ...prev]);
      setNickname('');
      setAccountNumber('');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not add beneficiary.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id) {
    setDeletingId(id);
    try {
      await api.delete(`/beneficiaries/${id}`);
      setList((prev) => prev.filter((b) => b.id !== id));
    } catch {
      setError('Could not remove that beneficiary.');
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Beneficiaries</h1>
        <p className="text-sm text-[var(--text-3)]">Save accounts you send to often.</p>
      </div>

      {error && (
        <p className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </p>
      )}

      <form onSubmit={handleAdd} className="glass rounded-2xl p-4 space-y-3">
        <div className="input-field rounded-xl px-4 py-2.5">
          <input
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="Nickname"
            className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
          />
        </div>
        <div className="input-field rounded-xl px-4 py-2.5">
          <input
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
            placeholder="Account number"
            className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full rounded-full py-2.5 text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-60"
        >
          <UserPlus size={16} /> {submitting ? 'Adding...' : 'Add Beneficiary'}
        </button>
      </form>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {list.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
              No beneficiaries saved yet.
            </div>
          )}
          {list.map((b) => (
            <div key={b.id} className="glass rounded-2xl p-4 flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-medium">{b.nickname}</p>
                <p className="text-xs text-[var(--text-3)] font-mono">{b.account_number}</p>
              </div>
              <button
                onClick={() => handleDelete(b.id)}
                disabled={deletingId === b.id}
                className="text-[var(--text-3)] hover:text-[var(--danger)] shrink-0 disabled:opacity-50"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}