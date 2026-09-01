import { useEffect, useState } from 'react';
import { Check, X, ShieldAlert } from 'lucide-react';
import api from '../../api/client';

export default function AdminKyc() {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);
  const [rejectReasons, setRejectReasons] = useState({});
  const [showRejectFor, setShowRejectFor] = useState(null);

  async function load() {
    try {
      const res = await api.get('/admin/kyc/pending');
      setSubmissions(res.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleApprove(id) {
    setActioningId(id);
    try {
      await api.post(`/admin/kyc/${id}/approve`);
      setSubmissions((prev) => prev.filter((s) => s.id !== id));
    } finally {
      setActioningId(null);
    }
  }

  async function handleReject(id) {
    setActioningId(id);
    try {
      await api.post(`/admin/kyc/${id}/reject`, { reason: rejectReasons[id] || null });
      setSubmissions((prev) => prev.filter((s) => s.id !== id));
    } finally {
      setActioningId(null);
      setShowRejectFor(null);
    }
  }

  return (
    <div className="space-y-6 stagger">
      <div>
        <h1 className="font-display text-xl font-semibold mb-1">KYC Verifications</h1>
        <p className="text-sm text-[var(--text-3)]">{submissions.length} pending review</p>
      </div>

      {loading && <p className="text-sm text-[var(--text-3)]">Loading...</p>}

      {!loading && (
        <div className="space-y-3">
          {submissions.length === 0 && (
            <div className="glass rounded-2xl p-10 text-center text-sm text-[var(--text-3)]">
              No pending KYC submissions.
            </div>
          )}
          {submissions.map((s) => (
            <div key={s.id} className="glass rounded-2xl p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(251,191,36,0.15)', color: '#FBBF24' }}
                >
                  <ShieldAlert size={18} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium">{s.full_legal_name}</p>
                  <p className="text-xs text-[var(--text-3)] capitalize">
                    {s.id_type.replace('_', ' ')} · {s.id_number}
                  </p>
                </div>
              </div>
              <div className="text-xs text-[var(--text-3)] space-y-1 pl-1">
                <p>DOB: {s.date_of_birth}</p>
                <p>Address: {s.address}</p>
              </div>

              {showRejectFor === s.id ? (
                <div className="space-y-2">
                  <input
                    value={rejectReasons[s.id] || ''}
                    onChange={(e) => setRejectReasons((prev) => ({ ...prev, [s.id]: e.target.value }))}
                    placeholder="Reason for rejection (optional)"
                    className="input-field rounded-xl px-4 py-2 w-full text-xs bg-transparent outline-none"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleReject(s.id)}
                      disabled={actioningId === s.id}
                      className="flex-1 rounded-full py-2 text-xs font-medium disabled:opacity-60"
                      style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}
                    >
                      Confirm Reject
                    </button>
                    <button
                      onClick={() => setShowRejectFor(null)}
                      className="flex-1 rounded-full py-2 text-xs font-medium toggle-pill text-[var(--text-2)]"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApprove(s.id)}
                    disabled={actioningId === s.id}
                    className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                    style={{ background: 'rgba(52,211,153,0.15)', color: '#34D399' }}
                  >
                    <Check size={14} /> Approve
                  </button>
                  <button
                    onClick={() => setShowRejectFor(s.id)}
                    disabled={actioningId === s.id}
                    className="flex-1 rounded-full py-2 text-xs font-medium flex items-center justify-center gap-1.5 disabled:opacity-60"
                    style={{ background: 'rgba(251,113,133,0.15)', color: '#FB7185' }}
                  >
                    <X size={14} /> Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}