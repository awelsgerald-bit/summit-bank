import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatAccountNumber(num) {
  if (!num) return '—';
  return num.replace(/(\d{4})(?=\d)/g, '$1 ');
}

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()
    : '';

  return (
    <div className="max-w-lg mx-auto space-y-5 stagger">
      <div className="glass rounded-3xl p-8 text-center">
        <div className="w-16 h-16 rounded-full grad-primary flex items-center justify-center mx-auto mb-4 font-display text-xl font-semibold">
          {initials}
        </div>
        <h3 className="font-display text-lg font-medium">{user?.full_name}</h3>
        <p className="text-sm text-[var(--text-3)]">{user?.email}</p>
      </div>

      <div className="glass rounded-2xl divide-y divide-white/5">
        <Row label="Account number" value={formatAccountNumber(user?.account_number)} mono />
        <Row label="Date joined" value={formatDate(user?.created_at)} />
        <Row label="Account status" value="Active" />
      </div>

      <button
        onClick={handleLogout}
        className="w-full rounded-full py-3 text-sm font-medium border border-white/10 text-[var(--danger)] hover:bg-white/5 flex items-center justify-center gap-2 transition"
      >
        <LogOut size={16} />
        Log out
      </button>
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="px-6 py-4 flex items-center justify-between text-sm">
      <span className="text-[var(--text-3)]">{label}</span>
      <span className={mono ? 'font-mono' : ''}>{value}</span>
    </div>
  );
}