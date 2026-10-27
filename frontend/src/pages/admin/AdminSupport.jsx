import { useEffect, useState } from 'react';
import api from '../../api/client';
import { errorMessage, formatDateTime } from '../../utils/errors';

const FILTERS = [
  ['', 'All'],
  ['open', 'Open'],
  ['answered', 'Answered'],
  ['closed', 'Closed'],
];

export default function AdminSupport() {
  const [filter, setFilter] = useState('open');
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [drafts, setDrafts] = useState({});
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get('/admin/support/tickets', { params: filter ? { status: filter } : {} })
      .then((res) => !cancelled && setTickets(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Could not load tickets.')))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [filter]);

  function replace(updated) {
    setTickets((prev) =>
      prev.flatMap((t) => {
        if (t.id !== updated.id) return [t];
        const next = { ...t, ...updated };
        return filter && next.status !== filter ? [] : [next];
      })
    );
  }

  async function reply(id) {
    const text = (drafts[id] || '').trim();
    if (!text) return;
    setBusyId(id);
    setError('');
    try {
      const res = await api.post(`/admin/support/tickets/${id}/reply`, { reply: text });
      setDrafts((d) => ({ ...d, [id]: '' }));
      replace(res.data);
    } catch (err) {
      setError(errorMessage(err, 'Could not send the reply.'));
    } finally {
      setBusyId(null);
    }
  }

  async function close(id) {
    setBusyId(id);
    setError('');
    try {
      const res = await api.post(`/admin/support/tickets/${id}/close`);
      replace(res.data);
    } catch (err) {
      setError(errorMessage(err, 'Could not close the ticket.'));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Support messages</h1>
        <div className="flex gap-2 mt-3">
          {FILTERS.map(([value, label]) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1.5 rounded-full text-xs toggle-pill ${filter === value ? 'toggle-active' : 'text-[var(--text-2)]'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
      {!loading && tickets.length === 0 && (
        <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">No messages here.</div>
      )}

      <div className="space-y-3">
        {tickets.map((t) => (
          <div key={t.id} className="glass rounded-2xl p-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium">#{t.id} · {t.subject}</p>
                <p className="text-xs text-[var(--text-3)]">
                  {t.user_name} ({t.user_email}) · {t.category} · {formatDateTime(t.created_at)}
                </p>
              </div>
              <span className="text-[10px] uppercase tracking-wide text-[var(--text-2)] shrink-0">{t.status}</span>
            </div>
            <p className="text-sm whitespace-pre-wrap break-words">{t.message}</p>
            {t.admin_reply && (
              <div className="rounded-xl px-3 py-2.5 text-sm whitespace-pre-wrap break-words" style={{ background: 'rgba(124,58,237,0.12)' }}>
                <p className="text-[11px] text-[var(--pink-accent)] mb-1">Your reply · {formatDateTime(t.replied_at)}</p>
                {t.admin_reply}
              </div>
            )}
            {t.status !== 'closed' && (
              <div className="space-y-2">
                <textarea
                  value={drafts[t.id] || ''}
                  onChange={(e) => setDrafts((d) => ({ ...d, [t.id]: e.target.value }))}
                  rows={3}
                  maxLength={2000}
                  placeholder="Write a reply. The user gets it by email and in the app."
                  className="input-field rounded-xl px-4 py-3 w-full text-sm text-[var(--text-1)] bg-transparent outline-none resize-y"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => reply(t.id)}
                    disabled={busyId === t.id || !(drafts[t.id] || '').trim()}
                    className="btn-primary rounded-full px-4 py-2 text-xs font-medium"
                  >
                    Send reply
                  </button>
                  <button
                    onClick={() => close(t.id)}
                    disabled={busyId === t.id}
                    className="rounded-full px-4 py-2 text-xs border border-white/10 text-[var(--text-2)]"
                  >
                    Close ticket
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
