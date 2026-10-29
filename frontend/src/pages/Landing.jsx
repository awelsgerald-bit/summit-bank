import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import {
  Anchor, ArrowRight, BadgeCheck, CalendarClock, CreditCard, Gift, Lock, PiggyBank, QrCode, ShieldCheck, Smartphone, Sparkles, Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';

const FEATURES = [
  { icon: Zap, title: 'Instant transfers', text: 'Send money to any Summit account in seconds, with a name check before you confirm.' },
  { icon: PiggyBank, title: 'Save4Me', text: 'Put money aside in goal pots and fixed deposits that keep it out of reach until you need it.' },
  { icon: CalendarClock, title: 'Scheduled payments', text: 'Set rent, allowance or any bill once. We send it on time, every time.' },
  { icon: CreditCard, title: 'Virtual cards', text: 'Spend online with cards you can freeze and unfreeze in one tap.' },
  { icon: QrCode, title: 'Pay with QR', text: 'Show your code to get paid, or scan one to send. No typing account numbers.' },
  { icon: Gift, title: 'Refer and earn', text: 'Invite friends. When they make their first deposit, you both get a bonus.' },
];

const STEPS = [
  { n: '1', title: 'Create your account', text: 'Sign up with your email and phone number in under a minute.' },
  { n: '2', title: 'Fund your wallet', text: 'Deposit by bank transfer to your own dedicated account number.' },
  { n: '3', title: 'Send, save and spend', text: 'Move money, build savings and manage cards from one place.' },
];

const TRUST = [
  { icon: Lock, label: 'Transaction PIN on every payment' },
  { icon: ShieldCheck, label: 'Every transfer reviewed before it moves' },
  { icon: BadgeCheck, label: 'Identity verification' },
  { icon: Smartphone, label: 'Built for your phone' },
];

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5" aria-label="Summit Bank home">
      <span className="w-9 h-9 rounded-xl grad-primary flex items-center justify-center text-white shadow-lg">
        <Anchor size={18} strokeWidth={1.8} />
      </span>
      <span className="font-display text-lg tracking-tight">
        Summit <span className="grad-text font-semibold">Bank</span>
      </span>
    </Link>
  );
}

function HeroCard() {
  return (
    <div className="relative mx-auto w-full max-w-sm h-[360px] sm:h-[400px]" aria-hidden="true">
      <div className="absolute inset-x-6 top-10 h-56 rounded-3xl blur-3xl opacity-60" style={{ background: 'radial-gradient(circle, #7c3aed, transparent 70%)' }} />
      <div className="float-b absolute right-0 top-0 w-52 rounded-2xl glass p-4 shadow-2xl">
        <p className="text-[11px] text-[var(--text-3)]">Money received</p>
        <p className="font-mono text-lg font-semibold text-[var(--success)]">+₦25,000.00</p>
        <p className="text-[11px] text-[var(--text-3)]">From Tola A.</p>
      </div>
      <div
        className="float-a absolute left-0 top-16 w-[88%] rounded-3xl p-6 text-white shadow-2xl"
        style={{ background: 'linear-gradient(135deg, #5b21b6 0%, #3b0f8c 50%, #1b0e3a 100%)', border: '1px solid rgba(255,255,255,0.15)' }}
      >
        <div className="flex items-center justify-between">
          <span className="font-display text-sm tracking-tight">Summit Bank</span>
          <span className="flex">
            <span className="w-6 h-6 rounded-full bg-[#fb7185] opacity-90" />
            <span className="w-6 h-6 rounded-full bg-[#fbbf24] opacity-90 -ml-2.5" />
          </span>
        </div>
        <p className="text-[11px] text-white/60 mt-8">Available balance</p>
        <p className="font-mono text-2xl font-semibold">₦1,250,000.00</p>
        <p className="font-mono text-sm tracking-[0.2em] text-white/80 mt-6">5566 3993 7942</p>
      </div>
      <div className="float-b absolute left-6 bottom-0 w-56 rounded-2xl glass p-4 shadow-2xl">
        <p className="text-[11px] text-[var(--text-3)]">Save4Me · Rent pot</p>
        <div className="h-1.5 rounded-full bg-white/10 mt-2 overflow-hidden"><div className="h-full w-2/3 grad-primary rounded-full" /></div>
        <p className="text-[11px] text-[var(--text-2)] mt-1.5">₦400,000 of ₦600,000</p>
      </div>
    </div>
  );
}

export default function Landing() {
  const { user, loading } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (!loading && user) return <Navigate to="/dashboard" replace />;

  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <div className="landing-glow" />

      <header className={`fixed top-0 inset-x-0 z-40 transition ${scrolled ? 'glass shadow-lg' : ''}`}>
        <div className="max-w-6xl mx-auto flex items-center justify-between px-5 sm:px-8 h-16">
          <Logo />
          <nav className="hidden md:flex items-center gap-8 text-sm text-[var(--text-2)]">
            <a href="#features" className="hover:text-[var(--text-1)] transition">Features</a>
            <a href="#how" className="hover:text-[var(--text-1)] transition">How it works</a>
            <a href="#security" className="hover:text-[var(--text-1)] transition">Security</a>
          </nav>
          <div className="flex items-center gap-3 sm:gap-4">
            <ThemeToggle />
            <Link to="/login" className="text-sm text-[var(--text-2)] hover:text-[var(--text-1)] transition">Sign in</Link>
            <Link to="/register" className="btn-primary rounded-full px-4 sm:px-5 py-2 text-sm font-medium">Open account</Link>
          </div>
        </div>
      </header>

      <main className="relative">
        <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-28 sm:pt-36 pb-16 grid lg:grid-cols-2 gap-14 items-center">
          <div className="fade-in">
            <span className="inline-flex items-center gap-2 glass rounded-full px-3.5 py-1.5 text-xs text-[var(--text-2)]">
              <Sparkles size={13} /> Banking that moves at your pace
            </span>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.05] mt-6">
              Reach your <span className="grad-text">financial summit</span>
            </h1>
            <p className="text-base sm:text-lg text-[var(--text-2)] mt-5 max-w-xl leading-relaxed">
              Send, save and spend from one beautifully simple account. Your own account number, virtual cards, scheduled payments and savings goals.
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Link to="/register" className="btn-primary rounded-full px-7 py-3.5 text-sm font-medium flex items-center gap-2 shadow-xl">
                Open free account <ArrowRight size={16} />
              </Link>
              <Link to="/login" className="glass hover-lift rounded-full px-7 py-3.5 text-sm font-medium">Sign in</Link>
            </div>
            <ul className="flex flex-wrap gap-x-6 gap-y-2 mt-8 text-xs text-[var(--text-3)]">
              <li className="flex items-center gap-1.5"><BadgeCheck size={14} /> No monthly fees</li>
              <li className="flex items-center gap-1.5"><BadgeCheck size={14} /> Sign up in a minute</li>
              <li className="flex items-center gap-1.5"><BadgeCheck size={14} /> Dark and light mode</li>
            </ul>
          </div>
          <HeroCard />
        </section>

        <section className="max-w-6xl mx-auto px-5 sm:px-8 pb-8">
          <div className="glass rounded-3xl grid grid-cols-2 lg:grid-cols-4 gap-px overflow-hidden">
            {TRUST.map((t) => (
              <div key={t.label} className="flex items-center gap-3 p-5 text-sm text-[var(--text-2)]">
                <span className="w-9 h-9 rounded-xl grad-primary flex items-center justify-center shrink-0 text-white"><t.icon size={16} /></span>
                {t.label}
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="max-w-6xl mx-auto px-5 sm:px-8 py-20 scroll-mt-20">
          <div className="max-w-2xl">
            <p className="text-sm font-medium" style={{ color: 'var(--pink-accent)' }}>Features</p>
            <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight mt-3">Everything you need, nothing you don't</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
            {FEATURES.map((f) => (
              <div key={f.title} className="glass hover-lift rounded-3xl p-6">
                <span className="w-11 h-11 rounded-2xl grad-primary flex items-center justify-center text-white"><f.icon size={20} strokeWidth={1.8} /></span>
                <h3 className="font-display text-base font-medium mt-5">{f.title}</h3>
                <p className="text-sm text-[var(--text-2)] mt-2 leading-relaxed">{f.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="max-w-6xl mx-auto px-5 sm:px-8 py-16 scroll-mt-20">
          <p className="text-sm font-medium" style={{ color: 'var(--pink-accent)' }}>How it works</p>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight mt-3">Up and running in three steps</h2>
          <div className="grid md:grid-cols-3 gap-4 mt-10">
            {STEPS.map((s) => (
              <div key={s.n} className="panel rounded-3xl p-6">
                <span className="font-display text-4xl font-semibold grad-text">{s.n}</span>
                <h3 className="font-display text-base font-medium mt-3">{s.title}</h3>
                <p className="text-sm text-[var(--text-2)] mt-2 leading-relaxed">{s.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="security" className="max-w-6xl mx-auto px-5 sm:px-8 py-16 scroll-mt-20">
          <div className="panel rounded-[32px] p-8 sm:p-12 grid lg:grid-cols-2 gap-8 items-center">
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--pink-accent)' }}>Security</p>
              <h2 className="font-display text-3xl font-semibold tracking-tight mt-3">Your money is guarded at every step</h2>
              <p className="text-sm text-[var(--text-2)] mt-4 leading-relaxed">
                A personal transaction PIN protects every payment. Transfers are reviewed before money moves, wrong PIN tries lock the PIN, and every receipt is kept for you.
              </p>
            </div>
            <ul className="space-y-3">
              {['Transaction PIN with lockout after wrong tries', 'Name check before you send', 'Review before any transfer settles', 'Statements and receipts you can download'].map((x) => (
                <li key={x} className="flex items-center gap-3 text-sm text-[var(--text-2)]">
                  <span className="w-6 h-6 rounded-full grad-primary flex items-center justify-center shrink-0 text-white"><BadgeCheck size={14} /></span>{x}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-8 pb-24">
          <div className="grad-primary rounded-[32px] px-6 py-14 sm:py-16 text-center text-white shadow-2xl">
            <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight">Ready to climb?</h2>
            <p className="mt-3 text-white/80 text-sm sm:text-base">Open your Summit Bank account today.</p>
            <Link to="/register" className="inline-flex items-center gap-2 mt-8 rounded-full bg-white text-[#3b0f8c] px-8 py-3.5 text-sm font-semibold hover:scale-[1.03] transition">
              Get started <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/5 py-8">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[var(--text-3)]">
          <Logo />
          <p>© {new Date().getFullYear()} Summit Bank. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
