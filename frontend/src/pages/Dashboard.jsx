import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowDownLeft, ArrowUpRight, ArrowLeftRight, History as HistoryIcon } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import WalletCarousel from '../components/WalletCarousel';
import QuickAction from '../components/QuickAction';
import TransactionRow from '../components/TransactionRow';

const POLL_INTERVAL_MS = 12000;

export default function Dashboard() {
  const { user, refreshProfile } = useAuth();
  const { showToast } = useToast();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const lastSeenApprovedIdRef = useRef(null);
  const firstLoadRef = useRef(true);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await api.get('/transactions/history');
      const list = res.data;
      setTransactions(list.slice(0, 4));

         if (list.length > 0) {
        // Track the newest APPROVED transaction, not just newest overall,
        // since pending ones haven't actually moved money yet.
        const newestApproved = list.find((t) => t.status === 'approved');

        if (newestApproved && !firstLoadRef.current && newestApproved.id !== lastSeenApprovedIdRef.current) {
          const isIncoming =
            newestApproved.transaction_type === 'deposit' ||
            (newestApproved.transaction_type === 'transfer' && newestApproved.receiver_id === user.id);

          if (isIncoming) {
            const amount = Number(newestApproved.amount).toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });
            showToast('Money received', `+$${amount} · ${newestApproved.description || 'Incoming transfer'}`);
            refreshProfile();
          }
        }
        if (newestApproved) lastSeenApprovedIdRef.current = newestApproved.id;
      }
      firstLoadRef.current = false;
    } catch {
      // silently ignore poll failures; the next interval will retry
    } finally {
      setLoading(false);
    }
  }, [user, showToast, refreshProfile]);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchHistory]);

  if (!user) return null;

  return (
    <div className="space-y-7 stagger">
      <WalletCarousel
        usd={{
          accountNumber: user.account_number,
          cardHolder: user.full_name,
          balance: Number(user.balance),
          createdAt: user.created_at,
        }}
      />

      <div className="grid grid-cols-4 gap-3 sm:gap-4">
        <QuickAction to="/deposit" label="Deposit" icon={<ArrowDownLeft size={18} />} />
        <QuickAction to="/withdraw" label="Withdraw" icon={<ArrowUpRight size={18} />} />
        <QuickAction to="/transfer" label="Transfer" icon={<ArrowLeftRight size={18} />} />
        <QuickAction to="/history" label="History" icon={<HistoryIcon size={18} />} />
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-base font-medium">Recent activity</h3>
          <a href="/history" className="text-xs" style={{ color: 'var(--pink-accent)' }}>
            View all
          </a>
        </div>
        <div className="space-y-3">
          {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
          {!loading && transactions.length === 0 && (
            <div className="glass rounded-2xl p-8 text-center text-sm text-[var(--text-3)]">
              No transactions yet.
            </div>
          )}
          {transactions.map((tx) => (
            <TransactionRow key={tx.id} tx={tx} currentUserId={user.id} />
          ))}
        </div>
      </div>
    </div>
  );
}