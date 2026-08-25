import { QRCodeSVG } from 'qrcode.react';
import { Anchor } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Receive() {
  const { user } = useAuth();

  const qrPayload = JSON.stringify({
    type: 'summit_bank_account',
    account_number: user?.account_number,
    name: user?.full_name,
  });

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Receive Money</h1>
        <p className="text-sm text-[var(--text-3)]">Let someone scan this to send you money.</p>
      </div>

      <div className="glass rounded-3xl p-8 flex flex-col items-center text-center">
        <div className="bg-white rounded-2xl p-5 mb-6">
          <QRCodeSVG value={qrPayload} size={200} bgColor="#ffffff" fgColor="#1B0E3A" level="M" />
        </div>

        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 rounded-md grad-primary flex items-center justify-center">
            <Anchor size={12} />
          </div>
          <p className="font-display text-sm font-medium">{user?.full_name}</p>
        </div>
        <p className="text-xs text-[var(--text-3)] font-mono">{user?.account_number}</p>
      </div>
    </div>
  );
}