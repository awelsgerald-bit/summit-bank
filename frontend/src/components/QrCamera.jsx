import { useEffect, useRef, useState } from 'react';
import { Upload } from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';

const REGION_ID = 'qr-camera-region';
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

// The camera view for scanning a QR code, framed like the Summit Bank cards. It asks for camera
// permission when it appears. Calls onScan(text) once per mount.
export default function QrCamera({ onScan }) {
  const [problem, setProblem] = useState('');
  const [starting, setStarting] = useState(true);
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan; // the parent passes a new function each render; keep the camera running
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
      const config = { fps: 10, aspectRatio: 1 };
      let lastError = null;
      for (const camera of [{ facingMode: 'environment' }, { facingMode: 'user' }]) {
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
          if ((err?.name || '') === 'NotAllowedError') break;
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
      // clear() throws while the camera is still running, and an error thrown here blanks the whole
      // page. Stop first, and never let either step raise.
      const stopping = started ? Promise.resolve().then(() => scanner.stop()).catch(() => {}) : Promise.resolve();
      stopping.then(() => { try { scanner.clear(); } catch { /* nothing to clear */ } });
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
      try { reader.clear(); } catch { /* nothing to clear */ }
      if (!doneRef.current) {
        doneRef.current = true;
        onScanRef.current(text);
      }
    } catch {
      setProblem('No QR code was found in that picture. Try a clearer, closer one.');
    }
  }

  return (
    <div>
      <div className="scan-frame card-dark">
        <div id={REGION_ID} className="scan-video" />
        <span className="scan-corner tl" /><span className="scan-corner tr" />
        <span className="scan-corner bl" /><span className="scan-corner br" />
        {!problem && !starting && <span className="scan-line" />}
        {(starting || problem) && (
          <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm" style={{ color: '#cfc8e0' }} role={problem ? 'alert' : 'status'}>
            {problem || 'Starting the camera. Allow access if your browser asks.'}
          </div>
        )}
      </div>
      <div id={FILE_REGION_ID} className="hidden" />
      <label className="ghost-btn mt-4 w-full rounded-2xl py-3 text-xs flex items-center justify-center gap-2 cursor-pointer">
        <Upload size={14} /> Upload a picture of the QR code
        <input type="file" accept="image/*" className="sr-only" onChange={scanPicture} />
      </label>
    </div>
  );
}
