import { useEffect, useState } from 'react';
import { Check, X, CreditCard } from 'lucide-react';
import api from '../../api/client';

export default function AdminCards() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);

  async function load() {
    try {
      const res = await api.get('/admin/cards/pending');
      setCards(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAction(id, action) {
    setActioningId(id);
    try {
      await api.post(`/admin/cards/${id}/${action}`);
      setCards((prev) => prev.filter((c) => c.id !== id));
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Card Applications</h1>
        <p className="text-sm text-[var(--text-3)]">{cards.length} pending review</p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {cards.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No pending card applications.
            </div>
          )}
          {cards.map((card) => (
            <div key={card.id} className="glass rounded-2xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
                >
                  <CreditCard size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium capitalize">{card.card_type} Card</p>
                  <p className="text-xs text-[var(--text-3)]">
                    Applied {new Date(card.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(card.id, 'approve')}
                  disabled={actioningId === card.id}
                  className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                  style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
                >
                  <Check size={14} /> Approve
                </button>
                <button
                  onClick={() => handleAction(card.id, 'reject')}
                  disabled={actioningId === card.id}
                  className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                  style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}
                >
                  <X size={14} /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}