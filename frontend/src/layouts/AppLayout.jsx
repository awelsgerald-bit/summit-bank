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
      isActive ? 'bg-[#1c1530] text-white' : 'text-[var(--text-2)] hover:text-white hover:bg-white/5'
    }`;
  }

  return (
    <div className="min-h-screen flex">
      <aside className="no-print hidden lg:flex flex-col w-64 shrink-0 p-6 gap-1 sticky top-0 h-screen overflow-y-auto">
        <div className="flex items-center gap-2.5 mb-10 px-2">
          <div className="w-8 h-8 rounded-lg grad-primary flex items-center justify-center text-white">
            <Anchor size={16} strokeWidth={1.7} />
          </div>
          <span className="font-display text-[15px] font-semibold tracking-tight">Summit Bank</span>
        </div>

        {primaryNav.map((item) => (
          <NavLink key={item.to} to={item.to} className={navLinkClass}>
            <item.icon size={18} strokeWidth={1.7} />
            {item.label}
          </NavLink>
        ))}

        <p className="text-xs text-[var(--text-3)] px-4 mt-6 mb-1">More</p>
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

      <div className="flex-1 min-w-0 flex flex-col lg:pr-6 lg:py-6">
        <header className="no-print flex items-center justify-between px-5 sm:px-8 lg:px-2 pt-5 pb-4 lg:pt-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMoreOpen(true)}
              aria-label="Open menu"
              className="lg:hidden -ml-2 w-11 h-11 flex items-center justify-center text-[var(--text-1)] rounded-full hover:bg-white/5"
            >
              <Menu size={22} strokeWidth={1.8} />
            </button>
            <span className="hidden lg:block font-display text-sm text-[var(--text-3)]">Welcome back</span>
          </div>
          <span className="lg:hidden font-display text-base font-semibold">Summit Bank</span>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Bell size={18} className="hidden sm:block text-[var(--text-2)]" />
            <NavLink to="/profile" aria-label="Profile">
              <Avatar user={user} size={36} />
            </NavLink>
          </div>
        </header>

        <main className="sheet flex-1 rounded-t-[36px] lg:rounded-[32px] px-5 sm:px-8 pt-3 pb-36 lg:pt-8 lg:pb-10 shadow-2xl">
          <div className="w-10 h-1 rounded-full bg-[#c9c3d6] mx-auto mb-5 lg:hidden" aria-hidden="true" />
          <div className="max-w-5xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

      <nav
        aria-label="Quick navigation"
        className="no-print lg:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-20 rounded-full px-2.5 py-2 flex items-center justify-between shadow-2xl w-[min(92vw,380px)] bg-[#14101f] border border-[#2a2240]"
      >
        {bottomNav.map((item) =>
          item.center ? (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              className="-mt-7 w-14 h-14 rounded-full bg-[var(--rose)] text-[#1a1426] flex items-center justify-center shadow-xl transition active:scale-95"
            >
              <item.icon size={24} strokeWidth={1.8} />
            </NavLink>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              className={({ isActive }) =>
                `w-12 h-12 rounded-full flex items-center justify-center transition ${
                  isActive ? 'text-white bg-[#2a2240]' : 'text-[#9a92b3] hover:text-white'
                }`
              }
            >
              <item.icon size={21} strokeWidth={1.8} />
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
