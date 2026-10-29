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
  CreditCard,
  ShieldAlert,
  Landmark,
  Settings as SettingsIcon,
  FileText,
  Bookmark,
  LifeBuoy,
  Coins,
  CalendarClock,
  Gift,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import MoreMenuSheet from '../components/MoreMenuSheet';
import Avatar from '../components/Avatar';
import ThemeToggle from '../components/ThemeToggle';

const primaryNav = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/transfer', label: 'Send', icon: ArrowLeftRight },
  { to: '/history', label: 'Activity', icon: History },
  { to: '/profile', label: 'Profile', icon: User },
];

// The floating bar on phones: Home, Send, the QR code in the middle, Activity and Settings.
const bottomNav = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/transfer', label: 'Send', icon: ArrowLeftRight },
  { to: '/receive', label: 'QR code', icon: QrCode, center: true },
  { to: '/history', label: 'Activity', icon: History },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

// Anything added here automatically shows up in the desktop "More" section
// and the mobile More sheet — no other wiring needed for future features.
const moreNav = [
  { to: '/receive', label: 'Receive', icon: QrCode },
  { to: '/beneficiaries', label: 'Beneficiaries', icon: Users },
  { to: '/loans', label: 'Loans', icon: HandCoins },
  { to: '/save4me', label: 'Save4Me', icon: Coins },
  { to: '/fixed-deposits', label: 'Fixed Deposits', icon: PiggyBank },
  { to: '/cards', label: 'Cards', icon: CreditCard },
  { to: '/kyc', label: 'Verify Identity', icon: ShieldAlert },
  { to: '/bank-account', label: 'Bank Account', icon: Landmark },
  { to: '/saved-payments', label: 'Saved Payments', icon: Bookmark },
  { to: '/scheduled', label: 'Scheduled', icon: CalendarClock },
  { to: '/referrals', label: 'Refer & Earn', icon: Gift },
  { to: '/statements', label: 'Statements', icon: FileText },
  { to: '/contact', label: 'Contact us', icon: LifeBuoy },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [moreOpen, setMoreOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login');
  }

  function navLinkClass({ isActive }) {
    return `flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm transition ${
      isActive ? 'panel text-[var(--text-1)]' : 'text-[var(--text-2)] hover:text-[var(--text-1)]'
    }`;
  }

  return (
    <div className="min-h-screen flex">
      <aside className="no-print hidden lg:flex flex-col w-64 shrink-0 p-6 gap-1 sticky top-0 h-screen overflow-y-auto">
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
            <header className="no-print sticky top-0 z-30 flex items-center justify-between px-5 sm:px-8 py-4 border-b border-white/5 backdrop-blur-xl bg-[var(--panel)]/80">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setMoreOpen(true)}
                  aria-label="Open menu"
                  className="text-[var(--text-2)] lg:hidden -ml-1 p-1"
                >
                  <Menu size={22} strokeWidth={1.8} />
                </button>
                <span className="hidden lg:block font-display text-sm text-[var(--text-3)]">Dashboard</span>
              </div>
              <div className="flex items-center gap-4">
                <ThemeToggle />
                <Bell size={18} className="text-[var(--text-2)]" />
                <NavLink to="/profile" aria-label="Profile">
                  <Avatar user={user} size={32} />
                </NavLink>
              </div>
            </header>

            <main className="px-5 sm:px-8 py-6 sm:py-8 pb-36 lg:pb-10">
              <Outlet />
            </main>
          </div>
        </div>
      </div>

      <nav
        aria-label="Quick navigation"
        className="no-print lg:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-20 glass rounded-full px-2.5 py-2 flex items-center gap-1 shadow-2xl w-[min(92vw,380px)] justify-between"
      >
        {bottomNav.map((item) =>
          item.center ? (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              className="-mt-7 w-14 h-14 rounded-full grad-primary text-white flex items-center justify-center shadow-xl ring-4 ring-[var(--panel)] transition active:scale-95"
            >
              <item.icon size={24} strokeWidth={1.8} />
            </NavLink>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center gap-0.5 w-14 h-12 rounded-full text-[10px] transition ${
                  isActive ? 'text-[var(--text-1)] bg-[var(--glass)]' : 'text-[var(--text-3)]'
                }`
              }
            >
              <item.icon size={19} strokeWidth={1.8} />
              {item.label}
            </NavLink>
          )
        )}
      </nav>

      {moreOpen && (
        <MoreMenuSheet
          items={moreNav}
          isAdmin={user?.role === 'admin'}
          onLogout={handleLogout}
          onClose={() => setMoreOpen(false)}
        />
      )}
    </div>
  );
}