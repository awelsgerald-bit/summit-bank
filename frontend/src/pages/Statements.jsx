import { useCallback, useEffect, useState } from 'react';
import { Download, FileText, Printer } from 'lucide-react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { errorMessage, formatDateTime, formatMoney, isoDate } from '../utils/errors';

const DAY = 24 * 60 * 60 * 1000;

function presetRange(id) {
  const now = new Date();
  const today = isoDate(now);
  if (id === '30') return [isoDate(new Date(now - 29 * DAY)), today];
  if (id === '90') return [isoDate(new Date(now - 89 * DAY)), today];
  if (id === 'month') return [`${today.slice(0, 8)}01`, today];
  return ['', ''];
}

const PRESETS = [
  { id: '30', label: 'Last 30 days' },
  { id: '90', label: 'Last 90 days' },
  { id: 'month', label: 'This month' },
  { id: 'all', label: 'All time' },
];

export default function Statements() {
  const { user } = useAuth();
  const [[start, end], setRange] = useState(() => presetRange('30'));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  const params = useCallback(() => {
    const p = {};
    if (start) p.start = start;
    if (end) p.end = end;
    return p;
  }, [start, end]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError('');
      try {
        const res = await api.get('/statements', { params: params() });
        if (!cancelled) setData(res.data);
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(errorMessage(err, 'Could not load your statement.'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [params]);

  async function downloadCsv() {
    setDownloading(true);
    setError('');
    try {
      const res = await api.get('/statements/csv', { params: params(), responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `summit-statement-${start || 'start'}-to-${end || 'today'}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError('Could not download the file. Please try again.');
    } finally {
      setDownloading(false);
    }
  }

  const items = data?.items || [];

  return (
    <div className="space-y-6">
      <div className="no-print space-y-4">
        <h2 className="font-display text-lg font-medium">Statements</h2>

        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => setRange(presetRange(p.id))}
              className="px-3 py-1.5 rounded-full text-xs toggle-pill text-[var(--text-2)]"
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs text-[var(--text-3)]">
            From
            <input
              type="date"
              value={start}
              max={end || undefined}
              onChange={(e) => setRange([e.target.value, end])}
              className="input-field rounded-xl px-3 py-2 mt-1 block text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <label className="text-xs text-[var(--text-3)]">
            To
            <input
              type="date"
              value={end}
              min={start || undefined}
              onChange={(e) => setRange([start, e.target.value])}
              className="input-field rounded-xl px-3 py-2 mt-1 block text-sm text-[var(--text-1)] bg-transparent outline-none"
            />
          </label>
          <button
            onClick={downloadCsv}
            disabled={downloading || loading}
            className="btn-primary rounded-full px-4 py-2.5 text-sm font-medium flex items-center gap-2"
          >
            <Download size={15} /> {downloading ? 'Preparing...' : 'Download CSV'}
          </button>
          <button
            onClick={() => window.print()}
            disabled={loading || items.length === 0}
            className="rounded-full px-4 py-2.5 text-sm border border-white/10 text-[var(--text-1)] flex items-center gap-2 disabled:opacity-50"
          >
            <Printer size={15} /> Save as PDF
          </button>
        </div>
        <p className="text-xs text-[var(--text-3)]">
          For a PDF, choose "Save as PDF" as the printer in the window that opens.
        </p>
      </div>

      {error && (
        <div className="no-print text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
          {error}
        </div>
      )}
      {loading && <p className="no-print text-sm text-[var(--text-3)]">Loading statement...</p>}

      {!loading && data && (
        <div className="print-area space-y-4">
          <div className="glass rounded-2xl p-5 space-y-1">
            <p className="font-display text-base">Summit Bank statement</p>
            <p className="text-sm">{user?.full_name} · {user?.account_number}</p>
            <p className="text-xs text-[var(--text-3)]">
              Period: {start || 'beginning'} to {end || 'today'} · Dates in Nigerian time
            </p>
            <div className="flex gap-6 pt-2 text-sm">
              <span>Credits: <b className="text-[var(--success)]">{formatMoney(data.total_in)}</b></span>
              <span>Debits: <b>{formatMoney(data.total_out)}</b></span>
            </div>
            <p className="text-[11px] text-[var(--text-3)]">Totals count approved transactions only.</p>
          </div>

          {items.length === 0 ? (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No transactions in this period.
            </div>
          ) : (
            <div className="glass rounded-2xl overflow-x-auto">
              <table className="w-full text-sm min-w-[640px]">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wide text-[var(--text-3)]">
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Details</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Amount</th>
                    <th className="px-4 py-3 font-medium no-print" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {items.map((t) => (
                    <tr key={t.id}>
                      <td className="px-4 py-3 whitespace-nowrap text-xs">{formatDateTime(t.timestamp)}</td>
                      <td className="px-4 py-3">
                        <p className="capitalize">{t.type}{t.counterparty !== '—' ? ` · ${t.counterparty}` : ''}</p>
                        <p className="text-xs text-[var(--text-3)]">{t.reference}{t.description ? ` · ${t.description}` : ''}</p>
                      </td>
                      <td className="px-4 py-3 capitalize text-xs">{t.status}</td>
                      <td
                        className={`px-4 py-3 text-right font-mono whitespace-nowrap ${
                          t.direction === 'credit' && t.status === 'approved' ? 'text-[var(--success)]' : ''
                        }`}
                      >
                        {t.direction === 'credit' ? '+' : '−'}{formatMoney(t.amount, t.currency)}
                      </td>
                      <td className="px-4 py-3 no-print">
                        <Link to={`/receipt/${t.id}`} className="text-[var(--pink-accent)] hover:opacity-80" title="Receipt">
                          <FileText size={16} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {data.truncated && (
            <p className="text-xs text-[var(--danger)]">
              Only the newest 5,000 transactions are shown. Choose a shorter period to see the rest.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
