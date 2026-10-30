import { Link } from 'react-router-dom';
import {
  Anchor, ArrowRight, BadgeCheck, CalendarClock, CreditCard, Gift, Lock, PiggyBank, QrCode, ShieldCheck, FileText, Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';
import TiltCard from '../components/TiltCard';

const SERVICES = [
  { icon: Zap, title: 'Instant transfers', text: 'Send to any Summit account in seconds. We show the name before you confirm.' },
  { icon: PiggyBank, title: 'Save4Me', text: 'Set money aside in goal pots, or lock it in a fixed deposit.' },
  { icon: CalendarClock, title: 'Scheduled payments', text: 'Set rent or allowance once. It goes out on time, every time.' },
];

const STEPS = [
  { label: 'Step 1', text: 'Create your account with your email and phone number.' },
  { label: 'Step 2', text: 'Deposit by bank transfer to your own account number.' },
  { label: 'Step 3', text: 'Send, save and spend from one place.' },
];

const SAFE = [
  { icon: Lock, title: 'Transaction PIN', text: 'Every payment needs it, and wrong tries lock it.' },
  { icon: ShieldCheck, title: 'Reviewed transfers', text: 'Each transfer is checked before the money moves.' },
  { icon: BadgeCheck, title: 'Verified identity', text: 'Confirm who you are once and keep your account safe.' },
];

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-display font-semibold tracking-tight whitespace-nowrap text-sm sm:text-base" aria-label="Summit Bank home">
      <span className="w-8 h-8 rounded-lg bg-[var(--lp-ink)] text-[var(--lp-bg)] flex items-center justify-center">
        <Anchor size={16} strokeWidth={1.9} />
      </span>
      Summit Bank
    </Link>
  );
}

// A loose hand-drawn ring, drawn once when the page loads.
function Ring() {
  return (
    <svg className="hand-ring absolute -inset-x-3 -inset-y-1 w-[calc(100%+1.5rem)] h-[calc(100%+0.5rem)] pointer-events-none" viewBox="0 0 200 70" preserveAspectRatio="none" fill="none" aria-hidden="true">
      <path d="M12 38 C 8 14, 70 4, 118 6 C 168 8, 196 20, 190 40 C 184 60, 130 66, 84 64 C 36 62, 4 56, 10 36" stroke="#d88aa0" strokeWidth="2.5" strokeLinecap="round" pathLength="1" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const signedIn = Boolean(user);

  return (
    <div className="landing min-h-screen overflow-x-hidden">
      <header className="max-w-6xl mx-auto px-5 sm:px-8 h-20 flex items-center justify-between md:grid md:grid-cols-3">
        <nav aria-label="Sections" className="hidden md:flex items-center gap-7 text-xs font-medium text-[var(--lp-muted)]">
          <a href="#services" className="hover:text-[var(--lp-ink)] transition">Services</a>
          <a href="#how" className="hover:text-[var(--lp-ink)] transition">How it works</a>
          <a href="#security" className="hover:text-[var(--lp-ink)] transition">Security</a>
        </nav>
        <div className="md:justify-self-center"><Logo /></div>
        <div className="flex items-center gap-3 sm:gap-5 md:justify-self-end">
          <ThemeToggle />
          {signedIn ? (
            <Link to="/dashboard" className="rounded-full bg-[var(--lp-ink)] text-[var(--lp-bg)] px-5 py-2.5 text-sm font-medium">Dashboard</Link>
          ) : (
            <>
              <Link to="/login" className="hidden min-[400px]:inline text-sm font-medium text-[var(--lp-muted)] hover:text-[var(--lp-ink)] transition">Sign in</Link>
              <Link to="/register" className="rounded-full bg-[var(--lp-ink)] text-[var(--lp-bg)] px-4 sm:px-5 py-2.5 text-sm font-medium hover:opacity-90 transition">Open account</Link>
            </>
          )}
        </div>
      </header>

      <main>
        <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-10 sm:pt-16 pb-20 grid lg:grid-cols-2 gap-14 lg:gap-8 items-center">
          <div>
            <h1 className="font-display font-semibold tracking-tight text-5xl sm:text-6xl lg:text-7xl leading-[1.05]">
              Banking
              <span className="block mt-1">
                made{' '}
                <span className="relative inline-block px-1">
                  simple
                  <Ring />
                </span>
              </span>
            </h1>
            <p className="text-sm sm:text-base text-[var(--lp-muted)] mt-7 max-w-sm leading-relaxed">
              One account to send, save and spend. Get your own account number, virtual cards and savings goals in a single app.
            </p>
            <div className="flex items-center gap-5 mt-9">
              <Link to={signedIn ? '/dashboard' : '/register'} className="group flex items-center gap-3 text-sm font-semibold">
                <span className="w-12 h-12 bg-[var(--lp-ink)] text-[var(--lp-bg)] rounded-lg flex items-center justify-center shadow-xl transition group-hover:translate-x-1">
                  <ArrowRight size={18} />
                </span>
                {signedIn ? 'Go to your dashboard' : 'Open an account'}
              </Link>
              {!signedIn && <Link to="/login" className="text-sm font-medium text-[var(--lp-muted)] hover:text-[var(--lp-ink)] transition">Sign in</Link>}
            </div>
          </div>
          <TiltCard />
        </section>

        <section id="services" className="max-w-6xl mx-auto px-5 sm:px-8 py-14 scroll-mt-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-10">
          <h2 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight leading-tight sm:col-span-2 lg:col-span-1">
            Everything<br />in one place
          </h2>
          {SERVICES.map((s) => (
            <div key={s.title}>
              <s.icon size={22} strokeWidth={1.6} className="text-[#6a4fc0]" />
              <h3 className="font-display text-sm font-semibold mt-4">{s.title}</h3>
              <p className="text-xs text-[var(--lp-muted)] mt-2 leading-relaxed max-w-[230px]">{s.text}</p>
            </div>
          ))}
        </section>

        <section className="relative bg-[var(--lp-band)] mt-8">
          <span className="absolute left-1/2 -top-5 w-10 h-10 bg-[#b3a5e3] rounded-full" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 50%, 50% 50%, 50% 100%, 0 100%)' }} aria-hidden="true" />
          <div className="max-w-6xl mx-auto px-5 sm:px-8 py-20 grid sm:grid-cols-2 gap-12 sm:gap-24">
            <div>
              <CreditCard size={22} strokeWidth={1.6} className="text-[#6a4fc0]" />
              <h3 className="font-display text-lg font-semibold mt-4">Cards you control</h3>
              <p className="text-sm text-[var(--lp-muted)] mt-2 leading-relaxed max-w-xs">Spend online with virtual cards. Freeze and unfreeze them in one tap, any time.</p>
            </div>
            <div>
              <QrCode size={22} strokeWidth={1.6} className="text-[#6a4fc0]" />
              <h3 className="font-display text-lg font-semibold mt-4">Pay with a QR code</h3>
              <p className="text-sm text-[var(--lp-muted)] mt-2 leading-relaxed max-w-xs">Show your code to get paid, or scan one to send. No account numbers to type.</p>
            </div>
          </div>
        </section>

        <section id="how" className="max-w-6xl mx-auto px-5 sm:px-8 py-24 scroll-mt-4">
          <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight text-center">Up and running in minutes</h2>
          <ol className="mt-12 grid sm:grid-cols-3 border-y border-[var(--lp-line)] divide-y sm:divide-y-0 sm:divide-x divide-[var(--lp-line)]">
            {STEPS.map((s) => (
              <li key={s.label} className="px-6 py-8 text-center">
                <p className="text-xs text-[var(--lp-muted)]">{s.label}</p>
                <p className="font-display text-base font-semibold mt-3 leading-snug">{s.text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="max-w-6xl mx-auto px-5 sm:px-8 pb-24 grid lg:grid-cols-2 gap-14 items-center">
          <div className="relative">
            <div className="absolute inset-y-6 left-0 right-10 rounded-[28px] bg-[var(--lp-band)]" aria-hidden="true" />
            <div className="relative ml-6 sm:ml-10 mr-0 rounded-3xl bg-[var(--lp-card)] border border-[var(--lp-line)] shadow-[0_30px_60px_-30px_rgba(26,20,38,0.35)] p-6" aria-hidden="true">
              <div className="flex items-center justify-between text-sm">
                <span className="font-display font-semibold">Rent</span>
                <span className="font-display font-semibold">₦400,000</span>
              </div>
              <div className="h-2 rounded-full bg-[var(--lp-line)] mt-3 overflow-hidden"><div className="h-full w-2/3 rounded-full bg-[#4a3680]" /></div>
              <p className="text-xs text-[var(--lp-muted)] mt-2">Goal ₦600,000</p>
              <div className="flex items-center justify-between text-sm mt-6">
                <span className="font-display font-semibold">New laptop</span>
                <span className="font-display font-semibold">₦85,000</span>
              </div>
              <div className="h-2 rounded-full bg-[var(--lp-line)] mt-3 overflow-hidden"><div className="h-full w-1/4 rounded-full bg-[#b3a5e3]" /></div>
              <p className="text-xs text-[var(--lp-muted)] mt-2">Goal ₦350,000</p>
            </div>
          </div>
          <div>
            <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight leading-tight">Put your savings<br />on autopilot</h2>
            <ul className="mt-9 space-y-7">
              <li className="flex gap-4">
                <span className="w-9 h-9 rounded-full bg-[var(--lp-card)] border border-[var(--lp-line)] flex items-center justify-center shrink-0 text-[#6a4fc0]"><Gift size={16} /></span>
                <span><span className="block font-display text-sm font-semibold">Refer and earn</span><span className="block text-xs text-[var(--lp-muted)] mt-1 leading-relaxed">Invite a friend. When they make a first deposit, you both get a bonus.</span></span>
              </li>
              <li className="flex gap-4">
                <span className="w-9 h-9 rounded-full bg-[var(--lp-card)] border border-[var(--lp-line)] flex items-center justify-center shrink-0 text-[#6a4fc0]"><FileText size={16} /></span>
                <span><span className="block font-display text-sm font-semibold">Statements and receipts</span><span className="block text-xs text-[var(--lp-muted)] mt-1 leading-relaxed">Download a statement as PDF or CSV, and keep a receipt for every transfer.</span></span>
              </li>
            </ul>
          </div>
        </section>

        <section id="security" className="bg-[var(--lp-band)] scroll-mt-4">
          <div className="max-w-6xl mx-auto px-5 sm:px-8 py-20 grid lg:grid-cols-[1fr_2fr] gap-12">
            <h2 className="font-display text-3xl font-semibold tracking-tight leading-tight">Built to keep<br />your money safe</h2>
            <div className="grid sm:grid-cols-3 gap-8">
              {SAFE.map((s) => (
                <div key={s.title}>
                  <s.icon size={20} strokeWidth={1.7} className="text-[#6a4fc0]" />
                  <h3 className="font-display text-sm font-semibold mt-4">{s.title}</h3>
                  <p className="text-xs text-[var(--lp-muted)] mt-2 leading-relaxed">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-5 sm:px-8 py-24 text-center">
          <h2 className="font-display text-4xl sm:text-5xl font-semibold tracking-tight">Ready to climb?</h2>
          <p className="text-sm text-[var(--lp-muted)] mt-4">Open your Summit Bank account in about a minute.</p>
          <Link to={signedIn ? '/dashboard' : '/register'} className="inline-flex items-center gap-3 mt-9 rounded-full bg-[var(--lp-ink)] text-[var(--lp-bg)] px-8 py-4 text-sm font-semibold hover:opacity-90 transition">
            {signedIn ? 'Go to your dashboard' : 'Open an account'} <ArrowRight size={16} />
          </Link>
        </section>
      </main>

      <footer className="border-t border-[var(--lp-line)] py-8">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--lp-muted)]">
          <Logo />
          <nav aria-label="Footer" className="flex gap-6">
            <Link to="/login" className="hover:text-[var(--lp-ink)]">Sign in</Link>
            <Link to="/register" className="hover:text-[var(--lp-ink)]">Open account</Link>
            <a href="#services" className="hover:text-[var(--lp-ink)]">Services</a>
          </nav>
          <p>© {new Date().getFullYear()} Summit Bank</p>
        </div>
      </footer>
    </div>
  );
}
