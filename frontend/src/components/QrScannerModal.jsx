import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';

export default function QrScannerModal({ onScan, onClose }) {
  const containerId = 'qr-scanner-region';
  const scannerRef = useRef(null);

  useEffect(() => {
    const scanner = new Html5Qrcode(containerId);
    scannerRef.current = scanner;

    scanner
      .start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 220, height: 220 } },
        (decodedText) => {
          onScan(decodedText);
          scanner.stop().catch(() => {});
        },
        () => {} // ignore per-frame "no QR found" noise
      )
      .catch(() => {
        onScan(null, 'Could not access camera. Check permissions and try again.');
      });

    return () => {
      scannerRef.current?.stop().catch(() => {});
    };
  }, [onScan]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="panel rounded-3xl p-6 max-w-sm w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-base font-medium">Scan to Send</h3>
          <button onClick={onClose} className="text-[var(--text-2)]">
            <X size={20} />
          </button>
        </div>
        <div id={containerId} className="rounded-2xl overflow-hidden" />
        <p className="text-xs text-[var(--text-3)] text-center mt-4">
          Point your camera at a Summit Bank QR code
        </p>
      </div>
    </div>
  );
}