import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Upload, X } from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';

const REGION_ID = 'qr-scanner-region';
const FILE_REGION_ID = 'qr-file-region';

function cameraProblem(err) {
  const name = err?.name || '';
  const text = String(err?.message || err || '');
  if (!window.isSecureContext) return 'The camera only works on a secure (https) page.';
  if (name === 'NotAllowedError' || /permission|denied/i.test(text)) {
    return 'Camera access is blocked. Allow the camera for this site in your browser settings, then try again.';
  }
  if (name === 'NotFoundError' || /no camera|requested device not found/i.test(text)) {
    return 'No camera was found on this device. You can upload a picture of the QR code instead.';
  }
  if (name === 'NotReadableError' || /in use|could not start video/i.test(text)) {
    return 'The camera is being used by another app. Close it and try again.';
  }
  return 'Could not start the camera. You can upload a picture of the QR code instead.';
}

// Scans a Summit Bank QR code with the camera, or from a picture. Calls onScan(text) once,
// or onScan(null, message) when scanning cannot work.
export default function QrScannerModal({ onScan, onClose }) {
  const [problem, setProblem] = useState('');
  const [starting, setStarting] = useState(true);
  // The parent passes a new function on every render; keep the latest one without restarting the camera.
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;
  const doneRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    let started = false;
    const scanner = new Html5Qrcode(REGION_ID);

    function finish(text) {
      if (doneRef.current || cancelled) return;
      doneRef.current = true;
      onScanRef.current(text);
    }

    async function begin() {
      const config = { fps: 10, qrbox: (w, h) => { const side = Math.floor(Math.min(w, h) * 0.75); return { width: side, height: side }; } };
      const attempts = [{ facingMode: 'environment' }, { facingMode: 'user' }];
      let lastError = null;
      for (const camera of attempts) {
        if (cancelled) return;
        try {
          await scanner.start(camera, config, (text) => finish(text), () => {});
          started = true;
          if (cancelled) {
            await scanner.stop().catch(() => {});
            return;
          }
          setStarting(false);
          return;
        } catch (err) {
          lastError = err;
          if ((err?.name || '') === 'NotAllowedError') break; // asking again will not help
        }
      }
      if (!cancelled) {
        setStarting(false);
        setProblem(cameraProblem(lastError));
      }
    }
    begin();

    return () => {
      cancelled = true;
      if (started) scanner.stop().catch(() => {});
      scanner.clear?.();
    };
  }, []);

  async function scanPicture(e) {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setProblem('');
    try {
      const reader = new Html5Qrcode(FILE_REGION_ID);
      const text = await reader.scanFile(file, false);
      reader.clear?.();
      if (!doneRef.current) {
        doneRef.current = true;
        onScanRef.current(text);
      }
    } catch {
      setProblem('No QR code was found in that picture. Try a clearer, closer one.');
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" role="dialog" aria-modal="true" aria-label="Scan to send">
      <div className="panel rounded-3xl p-6 max-w-sm w-full">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-base font-medium">Scan to send</h3>
          <button onClick={onClose} aria-label="Close scanner" className="text-[var(--text-2)] w-9 h-9 flex items-center justify-center">
            <X size={20} />
          </button>
        </div>
        <div id={REGION_ID} className="rounded-2xl overflow-hidden bg-black/30 min-h-[200px]" />
        <div id={FILE_REGION_ID} className="hidden" />
        {starting && !problem && <p className="text-xs text-[var(--text-3)] text-center mt-3">Starting the camera. Allow access if your browser asks.</p>}
        {problem && <p className="text-sm text-[var(--danger)] text-center mt-3" role="alert">{problem}</p>}
        {!problem && !starting && (
          <p className="text-xs text-[var(--text-3)] text-center mt-3">Point your camera at a Summit Bank QR code</p>
        )}
        <label className="ghost-btn mt-4 w-full rounded-2xl py-2.5 text-xs flex items-center justify-center gap-2 cursor-pointer">
          <Upload size={14} /> Upload a picture of the QR code
          <input type="file" accept="image/*" className="sr-only" onChange={scanPicture} />
        </label>
      </div>
    </div>,
    document.body
  );
}
