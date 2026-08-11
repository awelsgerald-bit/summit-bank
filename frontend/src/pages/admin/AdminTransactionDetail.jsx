import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import api from '../../api/client';

function formatMoney(n) {
  return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AdminTransactionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tx, setTx] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get(`/admin/transactions/${id}`)
      .then((res) => setTx(res.data))
      .catch(() => setError('Could not load this transaction.'));
  }, [id]);

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/admin/transactions')} className="text-[var(--text-2)]">
          <ChevronLeft size={20} />
        </button>
        <h3 className="font-display text-lg font-medium">Receipt</h3>
      </div>

      {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

      {tx && (
        <div className="glass rounded-3xl p-8">
          <div className="text-center mb-6">
            <p className="text-xs text-[var(--text-3)] uppercase tracking-wide mb-1">
              {tx.transaction_type}
            </p>
            <p className="font-display text-3xl font-semibold">{formatMoney(tx.amount)}</p>
          </div>
          <div className="divide-y divide-white/5">
            <Row label="Transaction ID" value={`#${tx.id}`} />
            <Row label="Date" value={new Date(tx.timestamp).toLocaleString('en-US')} />
            <Row label="From" value={tx.sender_account_number || '—'} mono />
            <Row label="To" value={tx.receiver_account_number || '—'} mono />
            <Row label="Description" value={tx.description || '—'} />
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="py-3 flex items-center justify-between text-sm">
      <span className="text-[var(--text-3)]">{label}</span>
      <span className={mono ? 'font-mono' : ''}>{value}</span>
    </div>
  );
}