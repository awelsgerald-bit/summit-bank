import { useEffect, useState } from 'react';
import { CalendarClock, ChevronDown, Pause, Play, Plus, X } from 'lucide-react';
import api from '../api/client';
import RecipientLookup from '../components/RecipientLookup';
import { errorMessage, formatDateTime, formatMoney } from '../utils/errors';

const FREQUENCIES = [
  { value: 'once', label: 'Just once' },
  { value: 'daily', label: 'Every day' },
  { value: 'weekly', label: 'Every week' },
  { value: 'monthly', label: 'Every month' },
];
const FREQ_LABEL = Object.fromEntries(FREQUENCIES.map((f) => [f.value, f.label]));
const OUTCOME_LABEL = { created: 'Sent for approval', failed: 'Failed', claimed: 'Started' };

// A date + time typed in the box is Nigerian time; the server treats a time without a zone that way.
function inputToApi(value) {
  return value ? `${value}:00` : undefined;
}

function Field({ label, children }) {
  return (
    <label className="block text-xs text-[var(--text-3)]">
      {label}
      {children}
    </label>
  );
}
const inputClass =
  'input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none';

export default function ScheduledTransfers() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busyId, setBusyId] = useState(null);
  const [openId, setOpenId] = useState(null);
  const [runs, setRuns] = useState({});

  const [showForm, setShowForm] = useState(false);
  const [account, setAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [frequency, setFrequency] = useState('monthly');
  const [firstRun, setFirstRun] = useState('');
  const [endAt, setEndAt] = useState('');
  const [description, setDescription] = useState('');
  const [lookup, setLookup] = useState(null);
  const [saving, setSaving] = useState(false);

  async function load() {
    const res = await api.get('/scheduled-transfers');
    setItems(res.data);
  }

  useEffect(() => {
    load()
      .catch((err) => setError(errorMessage(err, 'Could not load your scheduled transfers.')))
      .finally(() => setLoading(false));
  }, []);

  async function create(e) {
    e.preventDefault();
    setError('');
    setNotice('');
    if (lookup?.is_self || lookup?.not_found) {
      setError(lookup.is_self ? "You can't schedule a transfer to your own account." : 'No Summit Bank account has that number.');
      return;
    }
    setSaving(true);
    try {
      await api.post('/scheduled-transfers', {
        recipient_account_number: account.trim(),
        amount: parseFloat(amount),
        frequency,
        first_run_at: inputToApi(firstRun),
        end_at: frequency === 'once' ? undefined : inputToApi(endAt),
        description: description.trim() || undefined,
      });
      await load();
      setAccount('');
      setAmount('');
      setFirstRun('');
      setEndAt('');
      setDescription('');
      setShowForm(false);
      setNotice('Scheduled. Each time it is due, the transfer is sent for admin approval, then the money moves.');
    } catch (err) {
      setError(errorMessage(err, 'Could not schedule this transfer.'));
    } finally {
      setSaving(false);
    }
  }

  async function act(id, action) {
    setError('');
    setNotice('');
    setBusyId(id);
    try {
      await api.post(`/scheduled-transfers/${id}/${action}`);
      await load();
    } catch (err) {
      setError(errorMessage(err, 'That did not work. Please try again.'));
    } finally {
      setBusyId(null);
    }
  }

  async function toggleRuns(id) {
    if (openId === id) {
      setOpenId(null);
      return;
    }
    setOpenId(id);
    try {
      const res = await api.get(`/scheduled-transfers/${id}/runs`);
      setRuns((r) => ({ ...r, [id]: res.data }));
    } catch (err) {
      setError(errorMessage(err, 'Could not load the history.'));
    }
  }

  const open = items.filter((i) => i.status === 'active' || i.status === 'paused');
  const done = items.filter((i) => i.status === 'completed' || i.status === 'cancelled');

  function card(item) {
    const live = item.status === 'active' || item.status === 'paused';
    return (
      <div key={item.id} className="glass rounded-2xl p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{item.recipient_name || 'Summit Bank customer'}</p>
            <p className="text-xs text-[var(--text-3)]">
              <span className="font-mono">{item.recipient_account_number}</span> · {FREQ_LABEL[item.frequency]}
            </p>
            {item.description && <p className="text-xs text-[var(--text-3)] truncate">{item.description}</p>}
            <p className="text-[11px] text-[var(--text-3)]">
              {item.status === 'active' && `Next: ${formatDateTime(item.next_run_at)}`}
              {item.status === 'paused' && 'Paused'}
              {item.status === 'completed' && `Finished after ${item.run_count} ${item.run_count === 1 ? 'run' : 'runs'}`}
              {item.status === 'cancelled' && 'Cancelled'}
              {item.end_at && live ? ` · ends ${formatDateTime(item.end_at)}` : ''}
            </p>
            {item.last_status === 'failed' && (
              <p className="text-[11px] text-[var(--danger)]">Last run failed: {item.last_error}</p>
            )}
          </div>
          <p className="font-mono text-sm font-semibold shrink-0">{formatMoney(item.amount)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {item.status === 'active' && (
            <button disabled={busyId === item.id} onClick={() => act(item.id, 'pause')} className="ghost-btn rounded-full px-3 py-1.5 text-xs flex items-center gap-1">
              <Pause size={12} /> Pause
            </button>
          )}
          {item.status === 'paused' && (
            <button disabled={busyId === item.id} onClick={() => act(item.id, 'resume')} className="ghost-btn rounded-full px-3 py-1.5 text-xs flex items-center gap-1">
              <Play size={12} /> Resume
            </button>
          )}
          {live && (
            <button disabled={busyId === item.id} onClick={() => act(item.id, 'cancel')} className="ghost-btn rounded-full px-3 py-1.5 text-xs flex items-center gap-1">
              <X size={12} /> Cancel
            </button>
          )}
          <button onClick={() => toggleRuns(item.id)} className="ghost-btn rounded-full px-3 py-1.5 text-xs flex items-center gap-1">
            History <ChevronDown size={12} className={openId === item.id ? 'rotate-180' : ''} />
          </button>
        </div>
        {openId === item.id && (
          <div className="border-t border-[var(--border)] pt-2 space-y-1">
            {(runs[item.id] || []).length === 0 && <p className="text-xs text-[var(--text-3)]">Nothing has run yet.</p>}
            {(runs[item.id] || []).map((r) => (
              <div key={r.id} className="flex justify-between gap-3 text-xs">
                <span className="text-[var(--text-3)]">{formatDateTime(r.due_at)}</span>
                <span className={r.outcome === 'failed' ? 'text-[var(--danger)]' : ''}>
                  {OUTCOME_LABEL[r.outcome] || r.outcome}
                  {r.detail ? ` · ${r.detail}` : ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-lg font-medium">Scheduled transfers</h2>
          <p className="text-sm text-[var(--text-3)]">Send money later, or on repeat.</p>
        </div>
        <button onClick={() => setShowForm((s) => !s)} className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5">
          <Plus size={14} /> {showForm ? 'Close' : 'New'}
        </button>
      </div>

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">{error}</div>
      )}
      {notice && (
        <div className="text-sm text-[var(--success)] bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.25)] rounded-xl px-4 py-3">{notice}</div>
      )}

      {showForm && (
        <form onSubmit={create} className="glass rounded-3xl p-5 space-y-3">
          <Field label="Recipient account number">
            <input value={account} onChange={(e) => setAccount(e.target.value)} inputMode="numeric" required placeholder="0000000000" className={`${inputClass} font-mono`} />
          </Field>
          <RecipientLookup accountNumber={account} onResult={setLookup} />
          <Field label="Amount (₦)">
            <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required className={`${inputClass} font-mono`} />
          </Field>
          <Field label="How often">
            <select value={frequency} onChange={(e) => setFrequency(e.target.value)} className={inputClass}>
              {FREQUENCIES.map((f) => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </Field>
          <Field label={frequency === 'once' ? 'Send on (Nigerian time)' : 'First send (Nigerian time)'}>
            <input type="datetime-local" value={firstRun} onChange={(e) => setFirstRun(e.target.value)} required className={inputClass} />
          </Field>
          {frequency !== 'once' && (
            <Field label="Stop after (optional)">
              <input type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} className={inputClass} />
            </Field>
          )}
          <Field label="Description (optional)">
            <input value={description} onChange={(e) => setDescription(e.target.value)} maxLength={255} className={inputClass} />
          </Field>
          <p className="text-[11px] text-[var(--text-3)]">
            You will be asked for your transaction PIN. If your balance is too low on the day, that run is skipped and you are emailed.
          </p>
          <button disabled={saving} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
            {saving ? 'Scheduling...' : 'Schedule transfer'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && items.length === 0 && !showForm && (
        <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)] space-y-3">
          <CalendarClock className="mx-auto" size={22} />
          <p>Nothing scheduled yet. Tap New to set up rent, allowance or any repeat payment.</p>
        </div>
      )}

      <div className="space-y-3">{open.map(card)}</div>
      {done.length > 0 && (
        <>
          <p className="text-xs text-[var(--text-3)] pt-2">Finished</p>
          <div className="space-y-3">{done.map(card)}</div>
        </>
      )}
    </div>
  );
}
