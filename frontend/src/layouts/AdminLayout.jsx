import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Anchor, Users, Receipt, LogOut, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/admin/users', label: 'Users', icon: Users },
  { to: '/admin/transactions', label: 'Transactions', icon: Receipt },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen flex">
      <aside className="hidden lg:flex flex-col w-64 shrink-0 p-6 gap-1 sticky top-0 h-screen">
        <div className="flex items-center gap-2.5 mb-2 px-2">
          <div className="w-8 h-8 rounded-lg grad-primary flex items-center justify-center">
            <Anchor size={16} strokeWidth={1.7} />
          </div>
          <span className="font-display text-[15px] tracking-tight">
            Summit <span className="grad-text font-semibold">Bank</span>
          </span>
        </div>
        <div className="flex items-center gap-1.5 px-2 mb-8 text-[var(--pink-accent)]">
          <ShieldCheck size={13} />
          <span className="text-[11px] uppercase tracking-wider">Admin console</span>
        </div>

        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm transition ${
                isActive ? 'panel text-[var(--text-1)]' : 'text-[var(--text-2)] hover:text-[var(--text-1)]'
              }`
            }
          >
            <item.icon size={18} strokeWidth={1.7} />
            {item.label}
          </NavLink>
        ))}

        <div className="mt-auto space-y-1">
          <NavLink
            to="/dashboard"
            className="flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm text-[var(--text-2)] hover:text-[var(--text-1)]"
          >
            Back to my account
          </NavLink>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm text-[var(--text-2)] hover:text-[var(--danger)]"
          >
            <LogOut size={18} strokeWidth={1.7} />
            Log out
          </button>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex justify-center px-4 sm:px-6 py-6">
        <div className="w-full max-w-6xl">
          <div className="panel rounded-[32px] shadow-2xl overflow-hidden">
            <header className="flex items-center justify-between px-6 sm:px-8 py-5 border-b border-white/5">
              <span className="font-display text-sm text-[var(--text-3)]">Admin console</span>
              <div className="w-8 h-8 rounded-full grad-primary flex items-center justify-center text-xs font-semibold text-[#1B0E3A]">
                {user?.full_name?.[0]?.toUpperCase()}
              </div>
            </header>
            <main className="px-5 sm:px-8 py-6 sm:py-8">
              <Outlet />
            </main>
          </div>
        </div>
      </div>
    </div>
  );
}