import { useEffect, useState } from 'react';
import { Bookmark, Plus, Send, Trash2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import RecipientLookup from '../components/RecipientLookup';
import { errorMessage, formatDateTime, formatMoney } from '../utils/errors';

export default function SavedPayments() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [confirmId, setConfirmId] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const [showForm, setShowForm] = useState(false);
  const [label, setLabel] = useState('');
  const [account, setAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [lookup, setLookup] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get('/saved-payments')
      .then((res) => !cancelled && setItems(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Could not load your saved payments.')))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  async function save(e) {
    e.preventDefault();
    setError('');
    setNotice('');
    if (lookup?.is_self || lookup?.not_found) {
      setError(lookup.is_self ? "You can't save a payment to your own account." : 'No Summit Bank account has that number.');
      return;
    }
    setSaving(true);
    try {
      const res = await api.post('/saved-payments', {
        label: label.trim(),
        recipient_account_number: account.trim(),
        amount: parseFloat(amount),
        description: description.trim() || undefined,
      });
      setItems((prev) => [res.data, ...prev]);
      setLabel('');
      setAccount('');
      setAmount('');
      setDescription('');
      setShowForm(false);
    } catch (err) {
      setError(errorMessage(err, 'Could not save this payment.'));
    } finally {
      setSaving(false);
    }
  }

  async function pay(id) {
    setError('');
    setNotice('');
    setBusyId(id);
    try {
      await api.post(`/saved-payments/${id}/pay`);
      setConfirmId(null);
      setNotice('Payment submitted. It is pending admin approval, then the money moves.');
      const res = await api.get('/saved-payments');
      setItems(res.data);
    } catch (err) {
      setConfirmId(null);
      setError(errorMessage(err, 'Payment failed. Please try again.'));
    } finally {
      setBusyId(null);
    }
  }

  async function remove(id) {
    setError('');
    setBusyId(id);
    try {
      await api.delete(`/saved-payments/${id}`);
      setItems((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      setError(errorMessage(err, 'Could not delete it.'));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-lg font-medium">Saved payments</h2>
          <p className="text-sm text-[var(--text-3)]">Repeat a payment in one tap.</p>
        </div>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5"
        >
          <Plus size={14} /> {showForm ? 'Close' : 'New'}
        </button>
      </div>

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
        <form onSubmit={save} className="glass rounded-3xl p-5 space-y-3">
          <label className="block text-xs text-[var(--text-3)]">
            Name (for example "Rent")
            <input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              maxLength={60}
              required
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <label className="block text-xs text-[var(--text-3)]">
            Recipient account number
            <input
              value={account}
              onChange={(e) => setAccount(e.target.value)}
              inputMode="numeric"
              required
              placeholder="0000000000"
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm font-mono text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <RecipientLookup accountNumber={account} onResult={setLookup} />
          <label className="block text-xs text-[var(--text-3)]">
            Amount (₦)
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm font-mono text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <label className="block text-xs text-[var(--text-3)]">
            Description (optional)
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={255}
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <button disabled={saving} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
            {saving ? 'Saving...' : 'Save payment'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && items.length === 0 && !showForm && (
        <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)] space-y-3">
          <Bookmark className="mx-auto" size={22} />
          <p>No saved payments yet. Tap New, or save one after you send money.</p>
          <button onClick={() => navigate('/transfer')} className="ghost-btn rounded-full px-4 py-2 text-xs">
            Go to Send Money
          </button>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="glass rounded-2xl p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{item.label}</p>
                <p className="text-xs text-[var(--text-3)]">
                  {item.recipient_name} · <span className="font-mono">{item.recipient_account_number}</span>
                </p>
                {item.description && <p className="text-xs text-[var(--text-3)] truncate">{item.description}</p>}
                {item.last_paid_at && (
                  <p className="text-[11px] text-[var(--text-3)]">Last sent {formatDateTime(item.last_paid_at)}</p>
                )}
              </div>
              <p className="font-mono text-sm font-semibold shrink-0">{formatMoney(item.amount)}</p>
            </div>

            {confirmId === item.id ? (
              <div className="flex gap-2">
                <button
                  onClick={() => pay(item.id)}
                  disabled={busyId === item.id}
                  className="btn-primary flex-1 rounded-full py-2 text-xs font-medium"
                >
                  {busyId === item.id ? 'Sending...' : `Confirm: send ${formatMoney(item.amount)}`}
                </button>
                <button
                  onClick={() => setConfirmId(null)}
                  disabled={busyId === item.id}
                  className="flex-1 rounded-full py-2 text-xs border border-white/10 text-[var(--text-2)]"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setConfirmId(item.id)}
                  className="btn-primary flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5"
                >
                  <Send size={13} /> Pay again
                </button>
                <button
                  onClick={() => remove(item.id)}
                  disabled={busyId === item.id}
                  aria-label="Delete saved payment"
                  className="rounded-full px-4 py-2 text-xs border border-white/10 text-[var(--danger)]"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
