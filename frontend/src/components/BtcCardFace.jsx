import { Bitcoin, Clock } from 'lucide-react';
import Blobs from './Blobs';

export default function BtcCardFace() {
  return (
    <div className="relative card-glow h-full">
      <div
        className="rounded-[28px] p-6 sm:p-7 relative overflow-hidden shadow-2xl h-full flex flex-col items-center justify-center text-center gap-3"
        style={{
          background: '#14101F',
          border: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <Blobs name="card" />
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