import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Check } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import BankCard from '../components/BankCard';

export default function Transfer() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [recipientAccount, setRecipientAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    const numericAmount = parseFloat(amount);
    if (!numericAmount || numericAmount <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }
    if (!recipientAccount.trim()) {
      setError('Enter a recipient account number.');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/transactions/transfer', {
        recipient_account_number: recipientAccount.trim(),
        amount: numericAmount,
        description: description || undefined,
      });
      await refreshProfile();
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 1400);
    } catch (err) {
      setError(err.response?.data?.message || 'Transfer failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="max-w-lg mx-auto fade-in">
        <div className="glass rounded-3xl p-10 text-center">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}>
            <Check size={26} />
          </div>
          <h3 className="font-display text-lg font-medium mb-1">Transfer sent</h3>
          <p className="text-sm text-[var(--text-3)]">Taking you back to your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center gap-3 mb-1">
        <button onClick={() => navigate('/dashboard')} className="text-[var(--text-2)]">
          <ChevronLeft size={20} />
        </button>
        <h3 className="font-display text-lg font-medium">Send Money</h3>
      </div>
      <p className="text-sm text-[var(--text-3)] -mt-4">
        Transfers arrive instantly between Summit Bank accounts.
      </p>

      <BankCard
        accountNumber={user?.account_number}
        cardHolder={user?.full_name}
        balance={Number(user?.balance ?? 0)}
        createdAt={user?.created_at}
      />

      {error && (
        <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">Account Number</label>
          <div className="input-field rounded-xl px-4 py-3">
            <input
              required
              value={recipientAccount}
              onChange={(e) => setRecipientAccount(e.target.value)}
              placeholder="0000000000"
              className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">Enter Amount</label>
          <div className="input-field rounded-xl px-4 py-3 flex items-center gap-1">
            <span className="text-[var(--text-3)]">$</span>
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>
        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">Description (optional)</label>
          <div className="input-field rounded-xl px-4 py-3">
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's this for?"
              className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <div>
            <p className="text-[10px] text-[var(--text-3)] uppercase tracking-wide">Available Balance</p>
            <p className="font-display text-lg font-semibold">
              ${Number(user?.balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <button type="submit" disabled={submitting} className="btn-primary rounded-full px-8 py-3 text-sm font-medium">
            {submitting ? 'Sending...' : 'Send Money'}
          </button>
        </div>
      </form>
    </div>
  );
}