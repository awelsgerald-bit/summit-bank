import { Bitcoin, Clock } from 'lucide-react';

export default function BtcCardFace() {
  return (
    <div className="relative card-glow h-full">
      <div
        className="rounded-[28px] p-6 sm:p-7 relative overflow-hidden shadow-2xl h-full flex flex-col items-center justify-center text-center gap-3"
        style={{
          background: 'linear-gradient(135deg,#3B1F78 0%, #2A1458 55%, #1B0E3A 100%)',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <div className="absolute -right-14 -top-14 w-56 h-56 rounded-full bg-white/5 blur-2xl pointer-events-none" />
        <div className="relative w-12 h-12 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}>
          <Bitcoin size={22} />
        </div>
        <div className="relative">
          <p className="text-sm font-medium mb-1">BTC Wallet</p>
          <div className="flex items-center gap-1.5 justify-center text-[var(--text-3)]">
            <Clock size={12} />
            <p className="text-xs">Coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}