import { useEffect, useState } from 'react';
import { Fingerprint } from 'lucide-react';
import api from '../api/client';
import { biometricSupported, enableBiometric, forgetBiometricOnThisDevice, hasBiometricOnThisDevice } from '../utils/biometric';
import { errorMessage, formatDateTime } from '../utils/errors';

// Settings card: turn fingerprint / Face ID sign-in on or off for this device.
export default function BiometricCard() {
  const [supported, setSupported] = useState(null);
  const [devices, setDevices] = useState([]);
  const [password, setPassword] = useState('');
  const [note, setNote] = useState(null);
  const [busy, setBusy] = useState(false);

  function load() {
    api.get('/biometric/credentials').then((res) => setDevices(res.data)).catch(() => {});
  }

  useEffect(() => {
    biometricSupported().then(setSupported);
    load();
  }, []);

  async function turnOn(e) {
    e.preventDefault();
    setNote(null);
    setBusy(true);
    try {
      await enableBiometric(password, /iPhone|iPad/.test(navigator.userAgent) ? 'iPhone / iPad' : /Android/.test(navigator.userAgent) ? 'Android phone' : 'This computer');
      setPassword('');
      setNote({ type: 'ok', text: 'Done. You can now sign in with your fingerprint or face on this device.' });
      load();
    } catch (err) {
      setNote({ type: 'error', text: errorMessage(err, err.message || 'Could not turn it on.') });
    } finally {
      setBusy(false);
    }
  }

  async function remove(id) {
    try {
      await api.delete(`/biometric/credentials/${id}`);
      if (devices.length <= 1) forgetBiometricOnThisDevice();
      load();
    } catch (err) {
      setNote({ type: 'error', text: errorMessage(err, 'Could not remove it.') });
    }
  }

  return (
    <div className="glass rounded-3xl p-6 space-y-4">
      <h3 className="font-display text-sm text-[var(--text-2)] flex items-center gap-2"><Fingerprint size={14} /> Fingerprint / Face ID</h3>
      <p className="text-xs text-[var(--text-3)]">
        Sign in with your fingerprint or face instead of typing your password. Your transaction PIN is still needed to move money.
      </p>

      {supported === false && (
        <p className="text-xs text-[var(--text-3)]">This device or browser does not support it, or the site is not on https.</p>
      )}

      {devices.length > 0 && (
        <ul className="divide-y divide-white/5">
          {devices.map((d) => (
            <li key={d.id} className="py-3 flex items-center gap-3 text-sm">
              <div className="min-w-0 flex-1">
                <p>{d.label}</p>
                <p className="text-xs text-[var(--text-3)]">{d.last_used_at ? `Last used ${formatDateTime(d.last_used_at)}` : 'Not used yet'}</p>
              </div>
              <button onClick={() => remove(d.id)} className="text-xs text-[var(--danger)]">Remove</button>
            </li>
          ))}
        </ul>
      )}

      {supported && (
        <form onSubmit={turnOn} className="space-y-3">
          <label className="block text-xs text-[var(--text-3)]">
            Account password (to confirm it is you)
            <input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="input-field rounded-xl px-4 py-3 w-full mt-1 text-sm text-[var(--text-1)] bg-transparent outline-none" />
          </label>
          {note && <p className={`text-xs ${note.type === 'ok' ? 'text-[#34D399]' : 'text-[var(--danger)]'}`} role="status">{note.text}</p>}
          <button disabled={busy} className="btn-primary rounded-full px-5 py-2.5 text-sm font-medium">
            {busy ? 'Waiting for your fingerprint…' : hasBiometricOnThisDevice() ? 'Add this device again' : 'Turn on for this device'}
          </button>
        </form>
      )}
      {!supported && note && <p className="text-xs text-[var(--danger)]">{note.text}</p>}
    </div>
  );
}
