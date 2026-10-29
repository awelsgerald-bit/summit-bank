import { CreditCard, Eye, EyeOff } from 'lucide-react';
import Blobs from './Blobs';
import { useState } from 'react';
import useCountUp from '../hooks/useCountUp';

function formatMoney(n) {
  return '₦' + n.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatAccountNumber(num) {
  if (!num) return '•••• •••• ••';
  return num.replace(/(\d{4})(?=\d)/g, '$1 ');
}

function formatExpiry(createdAt) {
  if (!createdAt) return '••/••';
  const d = new Date(createdAt);
  d.setFullYear(d.getFullYear() + 4);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const yy = String(d.getFullYear()).slice(-2);
  return `${mm}/${yy}`;
}

export default function BankCard({ accountNumber, cardHolder, balance, createdAt }) {
  const [hidden, setHidden] = useState(false);
  const [displayValue, flashing] = useCountUp(balance ?? 0);

  return (
    <div className="relative card-glow">
      <div
        className="rounded-[28px] p-6 sm:p-7 relative overflow-hidden shadow-2xl"
        style={{
          background: '#14101F',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <Blobs name="card" />

        <div className="relative flex items-start justify-between mb-6">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">Available Balance</p>
            <div className="flex items-center gap-2">
              <h2
                className={`font-display text-2xl sm:text-3xl font-semibold balance-value ${flashing ? 'balance-flash balance-pulse' : ''}`}
              >
                {hidden ? '$••••••' : formatMoney(displayValue)}
              </h2>
              <button onClick={() => setHidden((h) => !h)} className="text-white/60 hover:text-white shrink-0">
                {hidden ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
          </div>
          <div className="flex items-center">
            <div className="w-6 h-6 rounded-full" style={{ background: '#E2C8A4', opacity: 0.95 }} />
            <div className="w-6 h-6 rounded-full -ml-3" style={{ background: '#D88AA0', opacity: 0.95 }} />
          </div>
        </div>

        <div className="relative flex items-center gap-3 mb-6 text-white/70">
          <CreditCard size={26} strokeWidth={1.5} />
        </div>

        <div className="relative mb-6">
          <p className="font-mono text-lg sm:text-xl tracking-[0.15em] text-white/90">
            {formatAccountNumber(accountNumber)}
          </p>
        </div>

        <div className="relative flex items-end justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">Card holder</p>
            <p className="text-sm font-medium">{cardHolder}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">Expires</p>
            <p className="text-sm font-mono">{formatExpiry(createdAt)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}