import { ArrowDownLeft, ArrowUpRight, ArrowLeftRight } from 'lucide-react';

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

  return (
    <div className="hover-lift glass rounded-2xl p-3.5 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: bg, color: tint }}
        >
          <Icon size={18} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{label}</p>
          <p className="text-xs text-[var(--text-3)] truncate">{tx.description || '—'}</p>
        </div>
      </div>
      <div className="text-right shrink-0">
        <p className={`text-sm font-semibold font-mono ${positive ? 'text-[var(--success)]' : 'text-[var(--text-1)]'}`}>
          {positive ? '+' : '−'}{formatMoney(tx.amount)}
        </p>
        <p className="text-[11px] text-[var(--text-3)]">{formatDate(tx.timestamp)}</p>
      </div>
    </div>
  );
}