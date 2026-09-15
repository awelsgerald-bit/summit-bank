import { useNavigate } from 'react-router-dom';
import { Bitcoin, Clock, ChevronLeft } from 'lucide-react';

export default function BtcWallet() {
  const navigate = useNavigate();

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/dashboard')} className="text-[var(--text-2)]">
          <ChevronLeft size={20} />
        </button>
        <h3 className="font-display text-lg font-medium">BTC Wallet</h3>
      </div>

      <div className="glass rounded-3xl p-10 text-center">
        <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
          <Bitcoin size={26} />
        </div>
        <h3 className="font-display text-lg font-medium mb-1">Coming Soon</h3>
        <p className="text-sm text-[var(--text-3)] mb-6 flex items-center justify-center gap-1.5">
          <Clock size={12} /> BTC wallet features are temporarily paused while we focus on other improvements.
        </p>
        <button onClick={() => navigate('/dashboard')} className="btn-primary rounded-full px-6 py-2.5 text-sm font-medium">
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}