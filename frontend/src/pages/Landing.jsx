import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import {
  Anchor, ArrowRight, BadgeCheck, CalendarClock, CreditCard, Gift, Lock, PiggyBank, QrCode, ShieldCheck, Smartphone, Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from '../components/ThemeToggle';
import Blobs from '../components/Blobs';

const OFFERS = [
  { icon: Zap, title: 'Instant transfers', text: 'Send money to any Summit account in seconds. We show the account name before you confirm.' },
  { icon: PiggyBank, title: 'Save4Me', text: 'Set money aside in goal pots, or lock it in a fixed deposit until you need it.' },
  { icon: CalendarClock, title: 'Scheduled payments', text: 'Set up rent, allowance or any repeat payment once. It goes out on time, every time.' },
  { icon: CreditCard, title: 'Virtual cards', text: 'Spend online with cards you can freeze and unfreeze in one tap.' },
  { icon: QrCode, title: 'Pay with QR', text: 'Show your code to get paid, or scan one to send. No account numbers to type.' },
  { icon: Gift, title: 'Refer and earn', text: 'Invite friends. When they make their first deposit, you both get a bonus.' },
];

const STEPS = [
  { title: 'Create your account', text: 'Sign up with your email and phone number. It takes about a minute.' },
  { title: 'Fund your wallet', text: 'Deposit by bank transfer to your own dedicated account number.' },
  { title: 'Send, save and spend', text: 'Move money, build savings and manage cards from one place.' },
];

const SAFEGUARDS = [
  { icon: Lock, text: 'A transaction PIN on every payment, with a lockout after wrong tries' },
  { icon: ShieldCheck, text: 'Every transfer is reviewed before the money moves' },
  { icon: BadgeCheck, text: 'Identity verification for your account' },
  { icon: Smartphone, text: 'Statements and receipts you can download any time' },
];

function Logo({ className = '' }) {
  return (
    <Link to="/" className={`flex items-center gap-2.5 ${className}`} aria-label="Summit Bank home">
      <span className="w-9 h-9 rounded-xl grad-primary flex items-center justify-center text-white">
        <Anchor size={18} strokeWidth={1.8} />
      </span>
      <span className="font-display text-lg font-semibold tracking-tight">Summit Bank</span>
    </Link>
  );
}

// A small card that shows the kind of thing the app does, drawn in the app's own style.
function PhoneArt() {
  return (
    <div className="relative mx-auto w-full max-w-[340px] aspect-[390/700] rounded-[44px] overflow-hidden bg-[var(--ink)] border border-white/10 shadow-2xl" aria-hidden="true">
      <Blobs name="welcome" />
      <div className="absolute left-6 top-14">
        <p className="font-display text-xl text-white/70">Your way</p>
        <p className="font-display text-3xl font-bold leading-tight">to the summit</p>
      </div>
      <div className="float-b absolute left-5 right-5 bottom-24 rounded-3xl bg-[rgba(20,16,31,0.95)] border border-white/10 p-4">
        <p className="text-[11px] text-white/60">Available balance</p>
        <p className="font-display text-2xl font-bold">₦75,850.00</p>
        <p className="text-[11px] tracking-[0.18em] text-white/70 mt-2">5566 3993 7942</p>
      </div>
      <span className="absolute right-5 bottom-6 rounded-full bg-[var(--rose)] text-[#1a1426] font-display font-semibold text-sm px-7 py-3">Start</span>
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
    <div className="relative overflow-x-hidden">
      <header className={`fixed top-0 inset-x-0 z-40 transition ${scrolled ? 'bg-[rgba(14,11,20,0.85)] backdrop-blur-xl border-b border-white/5' : ''}`}>
        <div className="max-w-6xl mx-auto flex items-center justify-between px-5 sm:px-8 h-16">
          <Logo />
          <nav aria-label="Sections" className="hidden md:flex items-center gap-8 text-sm text-[var(--text-2)]">
            <a href="#offers" className="hover:text-white transition">What we offer</a>
            <a href="#how" className="hover:text-white transition">How it works</a>
            <a href="#security" className="hover:text-white transition">Security</a>
          </nav>
          <div className="flex items-center gap-3 sm:gap-5">
            <ThemeToggle />
            <Link to="/login" className="text-sm text-[var(--text-2)] hover:text-white transition">Sign in</Link>
            <Link to="/register" className="btn-primary rounded-full px-5 py-2.5 text-sm font-semibold">Open account</Link>
          </div>
        </div>
      </header>

      <main>
        <section className="relative min-h-[100svh] max-w-6xl mx-auto px-5 sm:px-8 pt-28 pb-24 lg:pb-28 flex flex-col lg:grid lg:grid-cols-[1.1fr_0.9fr] gap-12 lg:items-center">
          <div className="lg:hidden absolute inset-0 opacity-90" aria-hidden="true"><Blobs name="welcome" /></div>
          <div className="relative flex flex-col justify-between flex-1 gap-10 lg:flex-none lg:justify-center lg:gap-10">
            <div>
              <h1 className="font-display tracking-tight">
                <span className="block text-2xl sm:text-3xl font-normal text-white/70">Your way</span>
                <span className="block text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] mt-1">to the summit</span>
              </h1>
              <p className="text-base sm:text-lg text-[#d9d3e8] lg:text-[var(--text-2)] mt-6 max-w-md leading-relaxed">
                One account to send, save and spend. Get your own account number, virtual cards, scheduled payments and savings goals.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <Link to="/register" className="btn-primary rounded-full px-8 py-4 text-base font-display font-semibold flex items-center gap-2">
                Open a free account <ArrowRight size={18} />
              </Link>
              <Link to="/login" className="rounded-full px-6 py-4 text-sm font-medium border border-white/20 bg-[rgba(14,11,20,0.5)] hover:bg-white/10 transition">
                I already have an account
              </Link>
            </div>
          </div>
          <div className="relative hidden lg:block"><PhoneArt /></div>
        </section>

        <div className="light-zone rounded-t-[40px] relative -mt-10 pt-4">
          <div className="w-10 h-1 rounded-full bg-[#d6d0e2] mx-auto mt-3" aria-hidden="true" />

          <section id="offers" className="max-w-6xl mx-auto px-5 sm:px-8 pt-16 pb-12 scroll-mt-16">
            <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight max-w-xl">What Summit Bank gives you</h2>
            <p className="text-[var(--text-2)] mt-3 max-w-lg">Everything you need for day-to-day money, in one place.</p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-10">
              {OFFERS.map((o) => (
                <article key={o.title} className="panel hover-lift rounded-3xl p-6">
                  <span className="w-11 h-11 rounded-2xl bg-[#e8e2f5] text-[#3b2a66] flex items-center justify-center">
                    <o.icon size={20} strokeWidth={1.8} />
                  </span>
                  <h3 className="font-display text-lg font-semibold mt-5">{o.title}</h3>
                  <p className="text-sm text-[var(--text-2)] mt-2 leading-relaxed">{o.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="how" className="max-w-6xl mx-auto px-5 sm:px-8 py-14 scroll-mt-16">
            <h2 className="font-display text-3xl sm:text-4xl font-semibold tracking-tight">Up and running in three steps</h2>
            <ol className="grid md:grid-cols-3 gap-4 mt-10">
              {STEPS.map((s, i) => (
                <li key={s.title} className="panel rounded-3xl p-6">
                  <span className="w-9 h-9 rounded-full bg-[#1c1530] text-white font-display font-semibold flex items-center justify-center text-sm">{i + 1}</span>
                  <h3 className="font-display text-lg font-semibold mt-4">{s.title}</h3>
                  <p className="text-sm text-[var(--text-2)] mt-2 leading-relaxed">{s.text}</p>
                </li>
              ))}
            </ol>
          </section>

          <section id="security" className="max-w-6xl mx-auto px-5 sm:px-8 py-14 scroll-mt-16">
            <div className="relative overflow-hidden rounded-[36px] bg-[var(--ink)] text-[var(--text-1)] p-8 sm:p-12 grid lg:grid-cols-2 gap-8 items-center">
              <Blobs name="corner" opacity={0.55} />
              <div className="relative">
                <h2 className="font-display text-3xl font-semibold tracking-tight text-white">Your money is guarded at every step</h2>
                <p className="text-sm text-[#b8b0cf] mt-4 leading-relaxed max-w-md">
                  You decide who can move your money, and we check each transfer before it settles.
                </p>
              </div>
              <ul className="relative space-y-4">
                {SAFEGUARDS.map((x) => (
                  <li key={x.text} className="flex items-start gap-3 text-sm text-[#d9d3e8]">
                    <span className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0"><x.icon size={16} /></span>
                    <span className="pt-1.5">{x.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="max-w-6xl mx-auto px-5 sm:px-8 pt-6 pb-20">
            <div className="rounded-[36px] bg-[var(--rose)] text-[#1a1426] px-6 py-14 text-center">
              <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Ready to climb?</h2>
              <p className="mt-3 text-[#3a2430]">Open your Summit Bank account in about a minute.</p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link to="/register" className="rounded-full bg-[#1a1426] text-white px-8 py-3.5 text-sm font-semibold hover:scale-[1.03] transition">Open account</Link>
                <Link to="/login" className="rounded-full border border-[#1a1426]/30 px-8 py-3.5 text-sm font-semibold hover:bg-[#1a1426]/5 transition">Sign in</Link>
              </div>
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-white/5 py-8">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--text-3)]">
          <Logo />
          <nav aria-label="Footer" className="flex gap-6">
            <Link to="/login" className="hover:text-white">Sign in</Link>
            <Link to="/register" className="hover:text-white">Open account</Link>
            <a href="#offers" className="hover:text-white">What we offer</a>
          </nav>
          <p>© {new Date().getFullYear()} Summit Bank</p>
        </div>
      </footer>
    </div>
  );
}
