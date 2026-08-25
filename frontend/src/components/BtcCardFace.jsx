import { useEffect, useState } from 'react';
import { Bitcoin, Eye, EyeOff, ArrowRight } from 'lucide-react';
import api from '../api/client';
import useCountUp from '../hooks/useCountUp';

function formatBTC(n) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 }) + ' BTC';
}
function formatUSD(n) {
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function BtcCardFace() {
  const [wallet, setWallet] = useState(null); // null = loading, false = not applied, object = applied
  const [rate, setRate] = useState(null);
  const [hidden, setHidden] = useState(false);
  const [applying, setApplying] = useState(false);
  const [amount, setAmount] = useState('');
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState('');

  const [displayBalance] = useCountUp(wallet ? Number(wallet.balance) : 0);

  async function loadWallet() {
    try {
      const res = await api.get('/wallets');
      const btc = res.data.find((w) => w.currency === 'BTC');
      setWallet(btc || false);
    } catch {
      setWallet(false);
    }
  }

  async function loadRate() {
    try {
      const res = await api.get('/wallets/rates/BTC');
      setRate(Number(res.data.rate_usd));
    } catch {
      setRate(null);
    }
  }

  useEffect(() => {
    loadWallet();
    loadRate();
  }, []);

  async function handleApply() {
    setApplying(true);
    setError('');
    try {
      await api.post('/wallets/apply', { currency: 'BTC' });
      await loadWallet();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not apply for a BTC wallet.');
    } finally {
      setApplying(false);
    }
  }

  async function handleConvert(e) {
    e.preventDefault();
    setError('');
    const numeric = parseFloat(amount);
    if (!numeric || numeric <= 0) {
      setError('Enter an amount greater than zero.');
      return;
    }
    setConverting(true);
    try {
      await api.post('/wallets/BTC/deposit', null, { params: { amount_usd: numeric } });
      setAmount('');
      await loadWallet();
    } catch (err) {
      setError(err.response?.data?.message || 'Conversion failed.');
    } finally {
      setConverting(false);
    }
  }

  function shell(children) {
    return (
      <div className="relative card-glow h-full">
        <div
          className="rounded-[28px] p-6 sm:p-7 relative overflow-hidden shadow-2xl h-full flex flex-col"
          style={{
            background: 'linear-gradient(135deg,#7A3B12 0%, #4A230B 55%, #1B0E3A 100%)',
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <div className="absolute -right-14 -top-14 w-56 h-56 rounded-full bg-white/5 blur-2xl" />
          {children}
        </div>
      </div>
    );
  }

  if (wallet === null) {
    return shell(<p className="relative text-sm text-white/60">Loading BTC wallet...</p>);
  }

  if (wallet === false) {
    return shell(
      <div className="relative flex flex-col items-center justify-center text-center h-full gap-4 py-4">
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center"
          style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
        >
          <Bitcoin size={24} />
        </div>
        <div>
          <p className="text-sm font-medium mb-1">No BTC wallet yet</p>
          <p className="text-xs text-white/50">Apply to start holding and converting Bitcoin.</p>
        </div>
        {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
        <button
          onClick={handleApply}
          disabled={applying}
          className="btn-primary rounded-full px-6 py-2.5 text-xs font-medium"
        >
          {applying ? 'Applying...' : 'Apply for BTC Wallet'}
        </button>
      </div>
    );
  }

  return shell(
    <>
      <div className="relative flex items-start justify-between mb-6">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">BTC Wallet</p>
          <div className="flex items-center gap-2">
            <h2 className="font-display text-xl sm:text-2xl font-semibold balance-value">
              {hidden ? '••••••' : formatBTC(displayBalance)}
            </h2>
            <button onClick={() => setHidden((h) => !h)} className="text-white/60 hover:text-white shrink-0">
              {hidden ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>
          {!hidden && rate && <p className="text-xs text-white/50 mt-1">≈ {formatUSD(displayBalance * rate)}</p>}
        </div>
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
          style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
        >
          <Bitcoin size={20} />
        </div>
      </div>

      <div className="relative mt-auto">
        {error && <p className="text-xs text-[var(--danger)] mb-2">{error}</p>}
        <form onSubmit={handleConvert} className="flex items-center gap-2">
          <div
            className="rounded-full px-4 py-2.5 flex items-center gap-1 flex-1"
            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)' }}
          >
            <span className="text-white/50 text-sm">$</span>
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              type="number"
              step="0.01"
              min="0.01"
              placeholder="Convert amount"
              className="bg-transparent w-full text-sm outline-none placeholder:text-white/40"
            />
          </div>
          <button
            type="submit"
            disabled={converting}
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-[#1B0E3A] disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg,#FDE68A,#FBBF24)' }}
          >
            <ArrowRight size={16} />
          </button>
        </form>
        {rate && <p className="text-[10px] text-white/40 mt-2">1 BTC ≈ {formatUSD(rate)}</p>}
      </div>
    </>
  );
}