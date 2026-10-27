import { useEffect, useState } from 'react';
import { MessageSquare } from 'lucide-react';
import api from '../api/client';
import { errorMessage, formatDateTime } from '../utils/errors';

const CATEGORIES = [
  ['general', 'General question'],
  ['payment', 'A payment or transfer'],
  ['card', 'My card'],
  ['account', 'My account'],
  ['other', 'Something else'],
];

const STATUS = {
  open: { label: 'Waiting for reply', color: '#FBBF24', bg: 'rgba(251,191,36,0.15)' },
  answered: { label: 'Answered', color: '#34D399', bg: 'rgba(52,211,153,0.15)' },
  closed: { label: 'Closed', color: '#9CA3AF', bg: 'rgba(156,163,175,0.15)' },
};

export default function Contact() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('general');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let cancelled = false;
    api
      .get('/support/tickets')
      .then((res) => !cancelled && setTickets(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Could not load your messages.')))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  async function send(e) {
    e.preventDefault();
    setError('');
    setNotice('');
    setSending(true);
    try {
      const res = await api.post('/support/tickets', { category, subject: subject.trim(), message: message.trim() });
      setTickets((prev) => [res.data, ...prev]);
      setSubject('');
      setMessage('');
      setNotice('Message sent. We will reply here, and by email.');
    } catch (err) {
      setError(errorMessage(err, 'Could not send your message.'));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div>
        <h2 className="font-display text-lg font-medium">Contact us</h2>
        <p className="text-sm text-[var(--text-3)]">Send us a message. Never include your password or PIN.</p>
      </div>

      <form onSubmit={send} className="glass rounded-3xl p-5 space-y-3">
        <label className="block text-xs text-[var(--text-3)]">
          What is it about?
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
          >
            {CATEGORIES.map(([value, text]) => (
              <option key={value} value={value} className="text-black">{text}</option>
            ))}
          </select>
        </label>
        <label className="block text-xs text-[var(--text-3)]">
          Subject
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            minLength={3}
            maxLength={120}
            required
            className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none"
          />
        </label>
        <label className="block text-xs text-[var(--text-3)]">
          Message
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            minLength={5}
            maxLength={2000}
            required
            rows={5}
            className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none resize-y"
          />
        </label>
        {error && <p className="text-sm text-[var(--danger)]">{error}</p>}
        {notice && <p className="text-sm text-[var(--success)]">{notice}</p>}
        <button disabled={sending} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
          {sending ? 'Sending...' : 'Send message'}
        </button>
      </form>

      <h3 className="font-display text-sm text-[var(--text-2)]">Your messages</h3>
      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
      {!loading && tickets.length === 0 && (
        <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
          <MessageSquare className="mx-auto mb-2" size={20} /> No messages yet.
        </div>
      )}
      <div className="space-y-3">
        {tickets.map((t) => {
          const meta = STATUS[t.status] || STATUS.open;
          return (
            <div key={t.id} className="glass rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium truncate">#{t.id} · {t.subject}</p>
                <span className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide shrink-0" style={{ background: meta.bg, color: meta.color }}>
                  {meta.label}
                </span>
              </div>
              <p className="text-xs text-[var(--text-3)]">{formatDateTime(t.created_at)}</p>
              <p className="text-sm whitespace-pre-wrap break-words">{t.message}</p>
              {t.admin_reply && (
                <div className="rounded-xl px-3 py-2.5 text-sm whitespace-pre-wrap break-words" style={{ background: 'rgba(124,58,237,0.12)' }}>
                  <p className="text-[11px] text-[var(--pink-accent)] mb-1">Summit Bank replied · {formatDateTime(t.replied_at)}</p>
                  {t.admin_reply}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
