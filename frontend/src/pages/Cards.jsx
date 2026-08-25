import { useEffect, useState } from 'react';
import { CreditCard, Clock, XCircle, Eye, EyeOff } from 'lucide-react';
import api from '../api/client';

const statusMeta = {
  pending: { label: 'Under Review', icon: Clock, tint: '#FBBF24', bg: 'rgba(251,191,36,0.15)' },
  approved: { label: 'Active', icon: CreditCard, tint: '#34D399', bg: 'rgba(52,211,153,0.15)' },
  rejected: { label: 'Rejected', icon: XCircle, tint: '#FB7185', bg: 'rgba(251,113,133,0.15)' },
};

function ApprovedCardFace({ card }) {
  const [revealed, setRevealed] = useState(false);

  return (
    <div className="relative card-glow">
      <div
        className="rounded-[24px] p-6 relative overflow-hidden shadow-2xl"
        style={{
          background: 'linear-gradient(135deg,#3B1F78 0%, #2A1458 55%, #1B0E3A 100%)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <div className="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/5 blur-2xl" />
        <div className="relative flex items-center justify-between mb-8">
          <span className="text-[10px] uppercase tracking-wider text-white/50 capitalize">
            {card.card_type} Card
          </span>
          <button onClick={() => setRevealed((r) => !r)} className="text-white/60 hover:text-white">
            {revealed ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        <p className="font-mono text-lg tracking-[0.1em] mb-6">
          {revealed ? card.card_number : '•••• •••• •••• ' + card.card_number.slice(-4)}
        </p>
        <div className="flex items-end justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">Expires</p>
            <p className="text-sm font-mono">
              {String(card.expiry_month).padStart(2, '0')}/{String(card.expiry_year).slice(-2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">CVV</p>
            <p className="text-sm font-mono">{revealed ? card.cvv : '•••'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Cards() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [applying, setApplying] = useState(false);

  async function load() {
    try {
      const res = await api.get('/cards');
      setCards(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleApply(cardType) {
    setError('');
    setApplying(true);
    try {
      const res = await api.post('/cards/apply', { card_type: cardType });
      setCards((prev) => [res.data, ...prev]);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit application.');
    } finally {
      setApplying(false);
    }
  }

  const hasPending = cards.some((c) => c.status === 'pending');

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Cards</h1>
        <p className="text-sm text-[var(--text-3)]">Apply for a virtual or physical card.</p>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {!hasPending && (
        <div className="flex gap-3">
          <button
            onClick={() => handleApply('virtual')}
            disabled={applying}
            className="btn-primary flex-1 rounded-2xl py-3 text-xs font-medium disabled:opacity-60"
          >
            Apply for Virtual Card
          </button>
          <button
            onClick={() => handleApply('physical')}
            disabled={applying}
            className="ghost-btn flex-1 rounded-2xl py-3 text-xs font-medium disabled:opacity-60"
          >
            Apply for Physical Card
          </button>
        </div>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-4">
          {cards.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
              No cards yet.
            </div>
          )}
          {cards.map((card) => {
            if (card.status === 'approved') {
              return <ApprovedCardFace key={card.id} card={card} />;
            }
            const meta = statusMeta[card.status];
            const Icon = meta.icon;
            return (
              <div key={card.id} className="glass rounded-2xl p-4 flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: meta.bg, color: meta.tint }}
                >
                  <Icon size={18} />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium capitalize">{card.card_type} Card</p>
                    <span
                      className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide"
                      style={{ background: meta.bg, color: meta.tint }}
                    >
                      {meta.label}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-3)]">
                    Applied {new Date(card.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}