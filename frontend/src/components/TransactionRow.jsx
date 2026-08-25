import { ArrowDownLeft, ArrowUpRight, ArrowLeftRight, Clock, X } from 'lucide-react';

function formatMoney(n) {
  return '$' + Math.abs(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function StatusBadge({ status }) {
  if (status === 'pending') {
    return (
      <span
        className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide"
        style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
      >
        <Clock size={10} /> Pending
      </span>
    );
  }
  if (status === 'rejected') {
    return (
      <span
        className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wide"
        style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}
      >
        <X size={10} /> Rejected
      </span>
    );
  }
  return null;
}

export default function TransactionRow({ tx, currentUserId }) {
  let label, positive, tint, bg, Icon;

  if (tx.transaction_type === 'deposit') {
    label = 'Deposit';
    positive = true;
    tint = '#34D399';
    bg = 'rgba(52,211,153,0.15)';
    Icon = ArrowDownLeft;
  } else if (tx.transaction_type === 'withdrawal') {
    label = 'Withdrawal';
    positive = false;
    tint = '#FB7185';
    bg = 'rgba(251,113,133,0.15)';
    Icon = ArrowUpRight;
  } else {
    const isSender = tx.sender_id === currentUserId;
    label = isSender ? 'Transfer sent' : 'Transfer received';
    positive = !isSender;
    tint = '#C4B5FD';
    bg = 'rgba(196,181,253,0.15)';
    Icon = ArrowLeftRight;
  }

  const isSettled = tx.status === 'approved';

  return (
    <div className={`hover-lift glass rounded-2xl p-3.5 flex items-center justify-between gap-4 ${!isSettled ? 'opacity-70' : ''}`}>
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: bg, color: tint }}
        >
          <Icon size={18} />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium truncate">{label}</p>
            <StatusBadge status={tx.status} />
          </div>
          <p className="text-xs text-[var(--text-3)] truncate">{tx.description || '—'}</p>
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className={`text-sm font-semibold font-mono ${positive && isSettled ? 'text-[var(--success)]' : 'text-[var(--text-1)]'}`}>
          {positive ? '+' : '−'}{formatMoney(tx.amount)}
        </p>
        <p className="text-[11px] text-[var(--text-3)]">{formatDate(tx.timestamp)}</p>
      </div>
    </div>
  );
}