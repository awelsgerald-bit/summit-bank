import { useEffect, useState } from 'react';
import { Check, Copy, Gift, Share2 } from 'lucide-react';
import api from '../api/client';
import { errorMessage, formatDateTime, formatMoney } from '../utils/errors';

const STATE_LABEL = {
  waiting: 'Waiting for first deposit',
  pending: 'Bonus pending approval',
  approved: 'Bonus paid',
  rejected: 'Bonus declined',
  none: 'No bonus',
};

export default function Referrals() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api
      .get('/referrals/me')
      .then((res) => setData(res.data))
      .catch((err) => setError(errorMessage(err, 'Could not load your referrals.')));
  }, []);

  const link = data ? `${window.location.origin}/register?ref=${data.code}` : '';

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Could not copy. Select the link and copy it by hand.');
    }
  }

  async function share() {
    const text = `Join me on Summit Bank. Use my code ${data.code} when you sign up: ${link}`;
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Summit Bank', text, url: link });
        return;
      } catch {
        return;
      }
    }
    copy();
  }

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div>
        <h2 className="font-display text-lg font-medium">Refer a friend</h2>
        <p className="text-sm text-[var(--text-3)]">You both get a bonus when they make their first deposit.</p>
      </div>

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">{error}</div>
      )}

      {data && (
        <>
          <div className="glass rounded-3xl p-5 space-y-4 text-center">
            <Gift className="mx-auto" size={22} />
            <div>
              <p className="text-xs text-[var(--text-3)]">Your code</p>
              <p className="font-mono text-2xl tracking-widest font-semibold">{data.code}</p>
            </div>
            <p className="text-xs text-[var(--text-3)] break-all">{link}</p>
            <div className="flex justify-center gap-2">
              <button onClick={copy} className="ghost-btn rounded-full px-4 py-2 text-xs flex items-center gap-1.5">
                {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy link'}
              </button>
              <button onClick={share} className="btn-primary rounded-full px-4 py-2 text-xs font-medium flex items-center gap-1.5">
                <Share2 size={14} /> Share
              </button>
            </div>
            <p className="text-[11px] text-[var(--text-3)]">
              Each of you gets {formatMoney(data.bonus_amount)} once your friend deposits at least {formatMoney(data.min_first_deposit)}.
              Bonuses are added after an admin approves them.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="glass rounded-2xl p-4">
              <p className="text-xs text-[var(--text-3)]">Friends invited</p>
              <p className="font-mono text-lg font-semibold">{data.invited_count}</p>
            </div>
            <div className="glass rounded-2xl p-4">
              <p className="text-xs text-[var(--text-3)]">Bonus earned</p>
              <p className="font-mono text-lg font-semibold">{formatMoney(data.earned)}</p>
            </div>
          </div>

          {data.items.length > 0 && (
            <div className="glass rounded-2xl divide-y divide-[var(--border)]">
              {data.items.map((item, i) => (
                <div key={i} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm truncate">{item.name}</p>
                    <p className="text-[11px] text-[var(--text-3)]">Joined {formatDateTime(item.joined_at)}</p>
                  </div>
                  <span className="text-xs text-[var(--text-2)] shrink-0">{STATE_LABEL[item.state] || item.state}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
