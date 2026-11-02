import { Link } from 'react-router-dom';
import { QrCode, ScanLine } from 'lucide-react';

// The two sides of QR payments: pay someone, or show your own code.
export default function QrSwitch({ active }) {
  const base = 'flex-1 rounded-full py-2.5 text-xs font-medium flex items-center justify-center gap-2 transition-colors';
  const on = `${base} grad-primary text-white`;
  const off = `${base} text-[var(--text-2)]`;
  return (
    <div className="toggle-pill rounded-full p-1 flex gap-1 max-w-sm mx-auto w-full">
      <Link to="/scan-pay" className={active === 'scan' ? on : off}><ScanLine size={14} /> Scan &amp; Pay</Link>
      <Link to="/receive" className={active === 'mine' ? on : off}><QrCode size={14} /> My QR code</Link>
    </div>
  );
}
