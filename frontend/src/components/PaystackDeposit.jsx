import { useState } from 'react';
import { CreditCard, Clock } from 'lucide-react';
import api from '../api/client';

export default function PaystackDeposit() {
  const [amount, setAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  async function handlePay(e) {
    e.preventDefault();
    setError('');
    const numeric = parseFloat(amount);
    if (!numeric || numeric <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/payments/paystack/initialize', { amount: numeric });
      // Redirect the whole page to Paystack's hosted checkout
      window.location.href = res.data.authorization_url;
    } catch (err) {
      setError(err.response?.data?.message || 'Could not start payment.');
      setSubmitting(false);
    }
  }

  return (
    <div className="glass rounded-3xl p-8 text-center">
      <div
        className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-5"
        style={{ background: 'rgba(196,181,253,0.15)', color: '#C4B5FD' }}
      >
        <CreditCard size={22} />
      </div>
      <h3 className="font-display text-lg font-medium mb-1">Pay with Card</h3>
      <p className="text-sm text-[var(--text-3)] mb-6">
        You'll be taken to Paystack's secure checkout to complete payment.
      </p>

      {error && <p className="text-xs text-[var(--danger)] mb-4">{error}</p>}

      <form onSubmit={handlePay}>
        <div className="input-field rounded-2xl px-6 py-5 flex items-center justify-center gap-2 mb-6">
          <span className="text-2xl text-[var(--text-3)]">$</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="bg-transparent text-center w-40 font-display text-4xl font-semibold outline-none placeholder:text-[var(--text-3)]"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full rounded-xl py-3 text-sm font-medium disabled:opacity-60"
        >
          {submitting ? 'Redirecting...' : 'Continue to Paystack'}
        </button>
      </form>

      <div className="flex items-center gap-2 justify-center mt-5 text-[var(--text-3)]">
        <Clock size={12} />
        <p className="text-[11px]">Payments still require admin approval before your balance updates.</p>
      </div>
    </div>
  );
}