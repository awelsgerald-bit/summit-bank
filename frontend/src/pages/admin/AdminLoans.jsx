import { useEffect, useState } from 'react';
import { Check, X, HandCoins } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AdminLoans() {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);

  async function load() {
    try {
      const res = await api.get('/admin/loans/pending');
      setLoans(res.data);
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
      await api.post(`/admin/loans/${id}/${action}`);
      setLoans((prev) => prev.filter((l) => l.id !== id));
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Loan Applications</h1>
        <p className="text-sm text-[var(--text-3)]">{loans.length} pending review</p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {loans.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No pending loan applications.
            </div>
          )}
          {loans.map((loan) => (
            <div key={loan.id} className="glass rounded-2xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
                >
                  <HandCoins size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium">{formatMoney(loan.principal_amount)}</p>
                  <p className="text-xs text-[var(--text-3)]">
                    {loan.term_months} months · {loan.interest_rate}% interest · {loan.purpose || 'No purpose given'}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(loan.id, 'approve')}
                  disabled={actioningId === loan.id}
                  className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                  style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
                >
                  <Check size={14} /> Approve
                </button>
                <button
                  onClick={() => handleAction(loan.id, 'reject')}
                  disabled={actioningId === loan.id}
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