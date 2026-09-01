import { useEffect, useState } from 'react';
import { ShieldCheck, Clock, XCircle, ShieldAlert } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const ID_TYPES = [
  { value: 'passport', label: 'Passport' },
  { value: 'national_id', label: 'National ID' },
  { value: 'drivers_license', label: "Driver's License" },
];

const statusMeta = {
  unverified: { label: 'Not Verified', icon: ShieldAlert, tint: '#7C7396', bg: 'rgba(124,115,150,0.15)' },
  pending: { label: 'Under Review', icon: Clock, tint: '#FBBF24', bg: 'rgba(251,191,36,0.15)' },
  verified: { label: 'Verified', icon: ShieldCheck, tint: '#34D399', bg: 'rgba(52,211,153,0.15)' },
};

export default function Kyc() {
  const { user, refreshProfile } = useAuth();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [fullLegalName, setFullLegalName] = useState('');
  const [dob, setDob] = useState('');
  const [idType, setIdType] = useState('passport');
  const [idNumber, setIdNumber] = useState('');
  const [address, setAddress] = useState('');

  async function load() {
    try {
      const res = await api.get('/kyc');
      setSubmissions(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const hasPending = submissions.some((s) => s.status === 'pending');
  const meta = statusMeta[user?.kyc_status || 'unverified'];
  const Icon = meta.icon;

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!fullLegalName || !dob || !idNumber || !address) {
      setError('Please fill in all fields.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post('/kyc/submit', {
        full_legal_name: fullLegalName,
        date_of_birth: dob,
        id_type: idType,
        id_number: idNumber,
        address,
      });
      setSubmissions((prev) => [res.data, ...prev]);
      await refreshProfile();
      setFullLegalName('');
      setDob('');
      setIdNumber('');
      setAddress('');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit KYC.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">Identity Verification</h1>
        <p className="text-sm text-[var(--text-3)]">Verify your identity to unlock full account features.</p>
      </div>

      <div className="glass rounded-2xl p-4 flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
          style={{ background: meta.bg, color: meta.tint }}
        >
          <Icon size={18} />
        </div>
        <div>
          <p className="text-sm font-medium">{meta.label}</p>
          {submissions[0]?.status === 'rejected' && submissions[0]?.rejection_reason && (
            <p className="text-xs text-[var(--danger)]">{submissions[0].rejection_reason}</p>
          )}
        </div>
      </div>

      {!hasPending && user?.kyc_status !== 'verified' && (
        <form onSubmit={handleSubmit} className="glass rounded-2xl p-4 space-y-3">
          {error && <p className="text-xs text-[var(--danger)]">{error}</p>}
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Full legal name</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <input
                value={fullLegalName}
                onChange={(e) => setFullLegalName(e.target.value)}
                className="bg-transparent w-full text-sm outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Date of birth</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="bg-transparent w-full text-sm outline-none"
                style={{ colorScheme: 'dark' }}
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">ID type</label>
            <select
              value={idType}
              onChange={(e) => setIdType(e.target.value)}
              className="input-field rounded-xl px-4 py-2.5 w-full text-sm bg-transparent outline-none"
              style={{ colorScheme: 'dark' }}
            >
              {ID_TYPES.map((t) => (
                <option key={t.value} value={t.value} className="bg-[#17122A]">
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">ID number</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <input
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value)}
                className="bg-transparent w-full text-sm font-mono outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[var(--text-2)] mb-1.5 block">Address</label>
            <div className="input-field rounded-xl px-4 py-2.5">
              <textarea
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                rows={2}
                className="bg-transparent w-full text-sm outline-none resize-none"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary w-full rounded-full py-2.5 text-sm font-medium disabled:opacity-60"
          >
            {submitting ? 'Submitting...' : 'Submit for Verification'}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}
    </div>
  );
}