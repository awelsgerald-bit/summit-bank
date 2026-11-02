import { useEffect, useRef, useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Anchor, Check, Copy, Download, Plus, Share2, X } from 'lucide-react';
import api from '../api/client';
import QrSwitch from '../components/QrSwitch';
import { errorMessage, formatDateTime, formatMoney } from '../utils/errors';

const INK = '#1B0E3A';

// Draws the QR with the person's name under it as a PNG, for download or sharing.
async function makePng(svgEl, lines) {
  const xml = new XMLSerializer().serializeToString(svgEl);
  const url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml' }));
  try {
    const img = await new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = reject;
      image.src = url;
    });
    const W = 900;
    const H = 1160;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = INK;
    ctx.textAlign = 'center';
    ctx.font = '600 44px Sora, Inter, sans-serif';
    ctx.fillText('Summit Bank', W / 2, 90);
    ctx.drawImage(img, 130, 140, 640, 640);
    ctx.font = '600 46px Sora, Inter, sans-serif';
    ctx.fillText(lines[0], W / 2, 870);
    ctx.font = '500 40px ui-monospace, monospace';
    ctx.fillText(lines[1], W / 2, 940);
    ctx.font = '400 32px Inter, sans-serif';
    ctx.fillStyle = '#6b6480';
    ctx.fillText(lines[2], W / 2, 1000);
    ctx.fillText('Scan with the Summit Bank app to pay', W / 2, 1090);
    return await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
  } finally {
    URL.revokeObjectURL(url);
  }
}

function QrCard({ payload, name, account, bank, extra }) {
  const wrap = useRef(null);
  const [note, setNote] = useState('');

  function flash(text) {
    setNote(text);
    setTimeout(() => setNote(''), 2200);
  }

  async function copyAccount() {
    try {
      await navigator.clipboard.writeText(account);
      flash('Account number copied');
    } catch {
      flash('Could not copy. Select the number and copy it.');
    }
  }

  async function png() {
    const svg = wrap.current?.querySelector('svg');
    if (!svg) throw new Error('no qr');
    return makePng(svg, [name, account, bank]);
  }

  async function download() {
    try {
      const blob = await png();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `summit-bank-qr-${account}.png`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(link.href), 4000);
    } catch {
      flash('Could not make the picture on this device.');
    }
  }

  async function share() {
    try {
      const blob = await png();
      const file = new File([blob], `summit-bank-qr-${account}.png`, { type: 'image/png' });
      if (navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: 'Pay me on Summit Bank', text: `Pay ${name} on Summit Bank` });
      } else if (navigator.share) {
        await navigator.share({ title: 'Pay me on Summit Bank', text: `Pay ${name} on Summit Bank. Account ${account}.` });
      } else {
        await navigator.clipboard.writeText(`Pay ${name} on Summit Bank. Account ${account}.`);
        flash('Details copied. Sharing is not supported here.');
      }
    } catch (err) {
      if (err?.name !== 'AbortError') flash('Could not share from this device.');
    }
  }

  return (
    <div className="glass rounded-3xl p-6 sm:p-8 flex flex-col items-center text-center">
      <div ref={wrap} className="bg-white rounded-2xl p-5 mb-5">
        <QRCodeSVG value={payload} size={210} bgColor="#ffffff" fgColor={INK} level="M" marginSize={0} />
      </div>
      <div className="flex items-center gap-2 mb-1">
        <div className="w-6 h-6 rounded-md grad-primary flex items-center justify-center"><Anchor size={12} /></div>
        <p className="font-display text-base font-medium">{name}</p>
      </div>
      <p className="text-sm font-mono">{account}</p>
      <p className="text-xs text-[var(--text-3)] mt-0.5">{bank}</p>
      {extra}
      <div className="grid grid-cols-3 gap-2 w-full mt-6">
        <button onClick={copyAccount} className="ghost-btn rounded-2xl py-3 text-xs flex flex-col items-center gap-1.5"><Copy size={16} /> Copy number</button>
        <button onClick={download} className="ghost-btn rounded-2xl py-3 text-xs flex flex-col items-center gap-1.5"><Download size={16} /> Download</button>
        <button onClick={share} className="ghost-btn rounded-2xl py-3 text-xs flex flex-col items-center gap-1.5"><Share2 size={16} /> Share</button>
      </div>
      <p className="text-xs text-[var(--text-3)] mt-3 min-h-[1rem]" role="status">{note}</p>
    </div>
  );
}

export default function Receive() {
  const [mine, setMine] = useState(null);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [minutes, setMinutes] = useState('60');
  const [saving, setSaving] = useState(false);
  const [openId, setOpenId] = useState(null);

  function loadRequests() {
    api.get('/qr/requests').then((res) => setRequests(res.data)).catch(() => {});
  }

  useEffect(() => {
    api.get('/qr/me').then((res) => setMine(res.data)).catch((err) => setError(errorMessage(err, 'Could not load your QR code.')));
    loadRequests();
  }, []);

  async function createRequest(e) {
    e.preventDefault();
    setError('');
    if (amount && !/^\d+(\.\d{1,2})?$/.test(amount)) return setError('Enter a valid amount, or leave it empty.');
    setSaving(true);
    try {
      const res = await api.post('/qr/requests', {
        amount: amount ? Number(amount).toFixed(2) : undefined,
        reference: reference || undefined,
        expires_minutes: Number(minutes),
      });
      setAmount('');
      setReference('');
      setShowForm(false);
      setOpenId(res.data.id);
      loadRequests();
    } catch (err) {
      setError(errorMessage(err, 'Could not create the request.'));
    } finally {
      setSaving(false);
    }
  }

  async function cancel(id) {
    try {
      await api.post(`/qr/requests/${id}/cancel`);
      if (openId === id) setOpenId(null);
      loadRequests();
    } catch (err) {
      setError(errorMessage(err, 'Could not cancel it.'));
    }
  }

  const opened = requests.find((r) => r.id === openId && r.status === 'open');

  return (
    <div className="max-w-lg mx-auto space-y-6 fade-in">
      <QrSwitch active="mine" />
      <div className="text-center">
        <h1 className="font-display text-xl font-semibold">My QR code</h1>
        <p className="text-sm text-[var(--text-3)] mt-1">Anyone with Summit Bank can scan this to pay you. It never changes.</p>
      </div>

      {error && <div className="text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3" role="alert">{error}</div>}

      {mine ? (
        <QrCard payload={mine.payload} name={mine.full_name} account={mine.account_number} bank={mine.bank_name} />
      ) : (
        !error && <div className="glass rounded-3xl h-80 animate-pulse" />
      )}

      <div className="glass rounded-3xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-sm">Request a specific amount</h2>
            <p className="text-xs text-[var(--text-3)] mt-0.5">A one-time code with an amount and reference. It expires.</p>
          </div>
          <button onClick={() => setShowForm((s) => !s)} aria-label={showForm ? 'Close' : 'New request'} className="w-9 h-9 rounded-full grad-primary flex items-center justify-center">
            {showForm ? <X size={16} /> : <Plus size={16} />}
          </button>
        </div>

        {showForm && (
          <form onSubmit={createRequest} className="space-y-3">
            <div className="input-field rounded-xl px-4 py-3 flex items-center gap-2">
              <span className="text-[var(--text-3)]">₦</span>
              <input inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ''))} placeholder="Amount (leave empty to let them choose)" aria-label="Amount" className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]" />
            </div>
            <div className="input-field rounded-xl px-4 py-3">
              <input maxLength={60} value={reference} onChange={(e) => setReference(e.target.value)} placeholder="Reference, e.g. Invoice 42 (optional)" aria-label="Reference" className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]" />
            </div>
            <div className="input-field rounded-xl px-4 py-3">
              <select value={minutes} onChange={(e) => setMinutes(e.target.value)} aria-label="Expires after" className="bg-transparent w-full text-sm outline-none">
                <option value="15">Expires in 15 minutes</option>
                <option value="60">Expires in 1 hour</option>
                <option value="1440">Expires in 1 day</option>
                <option value="10080">Expires in 7 days</option>
              </select>
            </div>
            <button disabled={saving} className="btn-primary w-full rounded-full py-3 text-sm font-medium">{saving ? 'Creating…' : 'Create QR request'}</button>
          </form>
        )}

        {opened && mine && (
          <QrCard
            payload={opened.payload}
            name={mine.full_name}
            account={mine.account_number}
            bank={mine.bank_name}
            extra={<p className="text-xs mt-3" style={{ color: 'var(--pink-accent)' }}>{opened.amount ? formatMoney(opened.amount) : 'Any amount'}{opened.reference ? ` · ${opened.reference}` : ''}</p>}
          />
        )}

        {requests.length > 0 && (
          <ul className="divide-y divide-white/5">
            {requests.slice(0, 8).map((r) => (
              <li key={r.id} className="py-3 flex items-center gap-3 text-sm">
                <div className="min-w-0 flex-1">
                  <p className="truncate">{r.amount ? formatMoney(r.amount) : 'Any amount'}{r.reference ? ` · ${r.reference}` : ''}</p>
                  <p className="text-xs text-[var(--text-3)]">
                    {r.status === 'open' ? `Expires ${formatDateTime(r.expires_at)}` : r.status[0].toUpperCase() + r.status.slice(1)}
                  </p>
                </div>
                {r.status === 'open' && (
                  <>
                    <button onClick={() => setOpenId(r.id === openId ? null : r.id)} className="text-xs text-[var(--pink-accent)]">{r.id === openId ? 'Hide' : 'Show'}</button>
                    <button onClick={() => cancel(r.id)} className="text-xs text-[var(--danger)]">Cancel</button>
                  </>
                )}
                {r.status === 'paid' && <Check size={14} className="text-[#34D399]" />}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
