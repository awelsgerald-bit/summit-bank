import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Check } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function AmountActionForm({ mode, title, endpoint, buttonLabel }) {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
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

    setSubmitting(true);
    try {
      await api.post(endpoint, {
        amount: numericAmount,
        description: description || undefined,
      });
      await refreshProfile();
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 1400);
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong. Please try again.');
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
          <h3 className="font-display text-lg font-medium mb-1">
            {mode === 'deposit' ? 'Deposit successful' : 'Withdrawal successful'}
          </h3>
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
        <h3 className="font-display text-lg font-medium">{title}</h3>
      </div>

      <div className="glass rounded-3xl p-8 text-center">
        {error && (
          <div className="mb-5 text-sm text-left text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="input-field rounded-2xl px-6 py-5 flex items-center justify-center gap-2 mb-4">
            <span className="text-2xl text-[var(--text-3)]">$</span>
            <input
              type="number"
              step="0.01"
              min="0.01"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="bg-transparent text-center w-40 font-display text-4xl font-semibold outline-none placeholder:text-[var(--text-3)]"
            />
          </div>

          <div className="input-field rounded-xl px-4 py-3 mb-6 text-left">
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
            />
          </div>

          <p className="text-xs text-[var(--text-3)] mb-6">
            Available balance:{' '}
            <span className="font-mono text-[var(--text-2)]">
              ${Number(user?.balance ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </p>

          <button type="submit" disabled={submitting} className="btn-primary w-full rounded-full py-3 text-sm font-medium">
            {submitting ? 'Processing...' : buttonLabel}
          </button>
        </form>
      </div>
    </div>
  );
}