import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  Anchor,
  Home,
  ArrowLeftRight,
  History,
  User,
  Users,
  LogOut,
  Bell,
  Menu,
  ShieldCheck,
  QrCode,
  HandCoins,
  PiggyBank,
  MoreHorizontal,
  CreditCard,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import MoreMenuSheet from '../components/MoreMenuSheet';

const primaryNav = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/transfer', label: 'Send', icon: ArrowLeftRight },
  { to: '/history', label: 'Activity', icon: History },
  { to: '/profile', label: 'Profile', icon: User },
];

// Anything added here automatically shows up in the desktop "More" section
// and the mobile More sheet — no other wiring needed for future features.
const moreNav = [
  { to: '/receive', label: 'Receive', icon: QrCode },
  { to: '/beneficiaries', label: 'Beneficiaries', icon: Users },
  { to: '/loans', label: 'Loans', icon: HandCoins },
  { to: '/fixed-deposits', label: 'Fixed Deposits', icon: PiggyBank },
  { to: '/cards', label: 'Cards', icon: CreditCard },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [moreOpen, setMoreOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()
    : '';

  function navLinkClass({ isActive }) {
    return `flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm transition ${
      isActive ? 'panel text-[var(--text-1)]' : 'text-[var(--text-2)] hover:text-[var(--text-1)]'
    }`;
  }

  return (
    <div className="min-h-screen flex">
      <aside className="hidden lg:flex flex-col w-64 shrink-0 p-6 gap-1 sticky top-0 h-screen overflow-y-auto">
        <div className="flex items-center gap-2.5 mb-10 px-2">
          <div className="w-8 h-8 rounded-lg grad-primary flex items-center justify-center">
            <Anchor size={16} strokeWidth={1.7} />
          </div>
          <span className="font-display text-[15px] tracking-tight">
            Summit <span className="grad-text font-semibold">Bank</span>
          </span>
        </div>

        {primaryNav.map((item) => (
          <NavLink key={item.to} to={item.to} className={navLinkClass}>
            <item.icon size={18} strokeWidth={1.7} />
            {item.label}
          </NavLink>
        ))}

        <p className="text-[10px] uppercase tracking-wider text-[var(--text-3)] px-4 mt-6 mb-1">More</p>
        {moreNav.map((item) => (
          <NavLink key={item.to} to={item.to} className={navLinkClass}>
            <item.icon size={18} strokeWidth={1.7} />
            {item.label}
          </NavLink>
        ))}

        {user?.role === 'admin' && (
          <NavLink
            to="/admin/users"
            className="flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm text-[var(--pink-accent)] hover:opacity-80 mt-6"
          >
            <ShieldCheck size={18} strokeWidth={1.7} />
            Admin console
          </NavLink>
        )}

        <div className="mt-auto pt-6">
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
              <div className="flex items-center gap-3">
                <Menu size={18} className="text-[var(--text-2)] lg:hidden" />
                <span className="hidden lg:block font-display text-sm text-[var(--text-3)]">Dashboard</span>
              </div>
              <div className="flex items-center gap-4">
                <Bell size={18} className="text-[var(--text-2)]" />
                <div className="w-8 h-8 rounded-full grad-primary flex items-center justify-center text-xs font-semibold text-[#1B0E3A]">
                  {initials}
                </div>
              </div>
            </header>

            <main className="px-5 sm:px-8 py-6 sm:py-8 pb-32 lg:pb-10">
              <Outlet />
            </main>
          </div>
        </div>
      </div>

      <nav className="lg:hidden fixed bottom-5 left-1/2 -translate-x-1/2 glass rounded-full px-6 py-3.5 flex gap-7 items-center z-20 shadow-2xl">
        {primaryNav.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? 'text-[#F5F3FF]' : 'text-[#7C7396]')}
          >
            <item.icon size={20} strokeWidth={1.7} />
          </NavLink>
        ))}
        <button onClick={() => setMoreOpen(true)} className="text-[#7C7396]">
          <MoreHorizontal size={20} strokeWidth={1.7} />
        </button>
      </nav>

      {moreOpen && <MoreMenuSheet items={moreNav} onClose={() => setMoreOpen(false)} />}
    </div>
  );
}