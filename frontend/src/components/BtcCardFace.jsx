import { useEffect, useState } from 'react';
import { Bitcoin, Eye, EyeOff, Clock, XCircle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import useCountUp from '../hooks/useCountUp';

function formatBTC(n) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 6, maximumFractionDigits: 6 }) + ' BTC';
}
function formatUSD(n) {
  return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function BtcCardFace() {
  const [wallet, setWallet] = useState(null); // null = loading
  const [latestApplication, setLatestApplication] = useState(null);
  const [rate, setRate] = useState(null);
  const [hidden, setHidden] = useState(false);

  const [reason, setReason] = useState('');
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState('');

  const [displayBalance] = useCountUp(wallet ? Number(wallet.balance) : 0);

  async function load() {
    try {
      const [walletsRes, appsRes] = await Promise.all([
        api.get('/wallets'),
        api.get('/wallets/applications'),
      ]);
      const btcWallet = walletsRes.data.find((w) => w.currency === 'BTC');
      setWallet(btcWallet || false);

      const btcApps = appsRes.data.filter((a) => a.currency === 'BTC');
      setLatestApplication(btcApps[0] || null);
    } catch {
      setWallet(false);
    }
  }

  useEffect(() => {
    load();
    api
      .get('/wallets/rates/BTC')
      .then((res) => setRate(Number(res.data.rate_usd)))
      .catch(() => {});
  }, []);

  async function handleApply(e) {
    e.preventDefault();
    setError('');
    setApplying(true);
    try {
      await api.post('/wallets/apply', { currency: 'BTC', reason: reason || undefined });
      await load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit application.');
    } finally {
      setApplying(false);
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
          <div className="absolute -right-14 -top-14 w-56 h-56 rounded-full bg-white/5 blur-2xl pointer-events-none" />
          {children}
        </div>
      </div>
    );
  }

  if (wallet === null) {
    return shell(<p className="relative text-sm text-white/60">Loading BTC wallet...</p>);
  }

  // No wallet yet — check application status
  if (wallet === false) {
    if (latestApplication?.status === 'pending') {
      return shell(
        <div className="relative flex flex-col items-center justify-center text-center h-full gap-3 py-4">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
            <Clock size={22} />
          </div>
          <p className="text-sm font-medium">Application under review</p>
          <p className="text-xs text-white/50">You'll get a BTC wallet once an admin approves this.</p>
        </div>
      );
    }

    return shell(
      <div className="relative flex flex-col h-full py-1">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
            <Bitcoin size={20} />
          </div>
          <div>
            <p className="text-sm font-medium">Apply for a BTC Wallet</p>
            {latestApplication?.status === 'rejected' && (
              <p className="text-xs text-[var(--danger)]">Previous application was rejected — you can reapply.</p>
            )}
          </div>
        </div>
        {error && <p className="text-xs text-[var(--danger)] mb-2">{error}</p>}
        <form onSubmit={handleApply} className="mt-auto space-y-2">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reason (optional)"
            rows={2}
            className="w-full rounded-xl px-3 py-2 text-xs bg-white/5 border border-white/10 outline-none placeholder:text-white/40 resize-none"
          />
          <button
            type="submit"
            disabled={applying}
            className="btn-primary w-full rounded-full py-2.5 text-xs font-medium disabled:opacity-60"
          >
            {applying ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>
      </div>
    );
  }

  // Wallet exists
  return shell(
    <>
      <div className="relative flex items-start justify-between mb-6">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-white/50 mb-1">BTC Wallet</p>
          <div className="flex items-center gap-2">
            <h2 id="btc-balance" className="font-display text-xl sm:text-2xl font-semibold balance-value">
              {hidden ? '••••••' : formatBTC(displayBalance)}
            </h2>
            <button onClick={() => setHidden((h) => !h)} className="text-white/60 hover:text-white shrink-0">
              {hidden ? <Eye size={16} /> : <EyeOff size={16} />}
            </button>
          </div>
          {!hidden && rate && <p className="text-xs text-white/50 mt-1">≈ {formatUSD(displayBalance * rate)}</p>}
        </div>
        <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
          <Bitcoin size={20} />
        </div>
      </div>

      <Link
        to="/btc-wallet"
        className="relative mt-auto btn-primary rounded-full py-2.5 text-xs font-medium flex items-center justify-center gap-1.5"
      >
        Manage BTC Wallet <ArrowRight size={14} />
      </Link>
      {rate && <p className="relative text-[10px] text-white/40 mt-2 text-center">1 BTC ≈ {formatUSD(rate)}</p>}
    </>
  );
} 