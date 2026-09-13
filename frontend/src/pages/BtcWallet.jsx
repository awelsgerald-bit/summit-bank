import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Clock, ArrowDownLeft, ArrowUpRight, ArrowLeftRight } from 'lucide-react';
import api from '../api/client';

function formatBTC(n) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 });
}

const TABS = [
  { id: 'deposit', label: 'Deposit', icon: ArrowDownLeft },
  { id: 'withdraw', label: 'Withdraw', icon: ArrowUpRight },
  { id: 'transfer', label: 'Transfer', icon: ArrowLeftRight },
];

export default function BtcWallet() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('deposit');
  const [wallet, setWallet] = useState(null);
  const [rate, setRate] = useState(null);

  const [amount, setAmount] = useState('');
  const [recipientAccount, setRecipientAccount] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function load() {
    const [walletsRes, rateRes] = await Promise.all([api.get('/wallets'), api.get('/wallets/rates/BTC')]);
    setWallet(walletsRes.data.find((w) => w.currency === 'BTC') || null);
    setRate(Number(rateRes.data.rate_usd));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    const numeric = parseFloat(amount);
    if (!numeric || numeric <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }
    if (tab === 'transfer' && !recipientAccount.trim()) {
      setError('Enter a recipient account number.');
      return;
    }

    setSubmitting(true);
    try {
      if (tab === 'deposit') {
        await api.post('/wallets/BTC/deposit', null, { params: { amount_ngn: numeric } });
      } else if (tab === 'withdraw') {
        await api.post('/wallets/BTC/withdraw', null, { params: { amount_btc: numeric } });
      } else {
        await api.post('/wallets/BTC/transfer', null, {
          params: { recipient_account_number: recipientAccount.trim(), amount_btc: numeric },
        });
      }
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="max-w-lg mx-auto fade-in">
        <div className="glass rounded-3xl p-10 text-center">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
            <Clock size={26} />
          </div>
          <h3 className="font-display text-lg font-medium mb-1">Submitted</h3>
          <p className="text-sm text-[var(--text-3)] mb-6">Pending admin approval before your BTC balance updates.</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary rounded-full px-6 py-2.5 text-sm font-medium">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/dashboard')} className="text-[var(--text-2)]">
          <ChevronLeft size={20} />
        </button>
        <h3 className="font-display text-lg font-medium">BTC Wallet</h3>
      </div>

      {wallet && (
        <div className="glass rounded-2xl p-4 flex items-center justify-between">
          <div>
            <p className="text-[10px] text-[var(--text-3)] uppercase tracking-wide">Balance</p>
            <p className="font-mono text-sm">{formatBTC(wallet.balance)} BTC</p>
          </div>
          {rate && <p className="text-xs text-[var(--text-3)]">1 BTC ≈ ₦{rate.toLocaleString()}</p>}
        </div>
      )}

      <div className="toggle-pill rounded-full p-1 flex">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => {
              setTab(t.id);
              setError('');
              setAmount('');
            }}
            className={`flex-1 text-xs font-medium py-2 rounded-full flex items-center justify-center gap-1.5 transition ${tab === t.id ? 'toggle-active' : 'text-[var(--text-2)]'}`}
          >
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="glass rounded-2xl p-4 space-y-3">
        {error && <p className="text-xs text-[var(--danger)]">{error}</p>}

        {tab === 'transfer' && (
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Recipient Account Number</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <input
                value={recipientAccount}
                onChange={(e) => setRecipientAccount(e.target.value)}
                placeholder="0000000000"
                className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
              />
            </div>
          </div>
        )}

        <div>
          <label className="text-xs text-[var(--text-2)] mb-1.5 block">
            {tab === 'deposit' ? 'Amount (NGN to convert)' : 'Amount (BTC)'}
          </label>
          <div className="input-field rounded-xl px-4 py-2.5 flex items-center gap-1">
            <span className="text-[var(--text-3)] text-sm">{tab === 'deposit' ? '₦' : '₿'}</span>
            <input
              type="number"
              step="0.00000001"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="bg-transparent w-full text-sm font-mono outline-none placeholder:text-[var(--text-3)]"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="btn-primary w-full rounded-full py-2.5 text-sm font-medium disabled:opacity-60"
        >
          {submitting ? 'Submitting...' : `Submit ${TABS.find((t) => t.id === tab).label}`}
        </button>
      </form>
    </div>
  );
}