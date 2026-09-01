import { useState } from 'react';
import { CreditCard, Wallet } from 'lucide-react';
import AmountActionForm from '../components/AmountActionForm';
import PaystackDeposit from '../components/PaystackDeposit';

export default function Deposit() {
  const [mode, setMode] = useState('manual');

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="toggle-pill rounded-full p-1 flex">
        <button
          onClick={() => setMode('manual')}
          className={`flex-1 text-xs font-medium py-2 rounded-full flex items-center justify-center gap-1.5 transition ${mode === 'manual' ? 'toggle-active' : 'text-[var(--text-2)]'}`}
        >
          <Wallet size={14} /> Manual
        </button>
        <button
          onClick={() => setMode('paystack')}
          className={`flex-1 text-xs font-medium py-2 rounded-full flex items-center justify-center gap-1.5 transition ${mode === 'paystack' ? 'toggle-active' : 'text-[var(--text-2)]'}`}
        >
          <CreditCard size={14} /> Pay with Card
        </button>
      </div>

      {mode === 'manual' ? (
        <AmountActionForm mode="deposit" title="Deposit Funds" endpoint="/transactions/deposit" buttonLabel="Add Fund" />
      ) : (
        <PaystackDeposit />
      )}
    </div>
  );
}