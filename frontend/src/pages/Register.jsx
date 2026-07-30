import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Anchor, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await register(fullName, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not create your account.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center px-5 py-10">
      <div className="relative w-full max-w-md fade-in">
        <div className="flex items-center gap-3 justify-center mb-8">
          <div className="w-10 h-10 rounded-xl grad-primary flex items-center justify-center">
            <Anchor size={20} strokeWidth={1.7} />
          </div>
          <span className="font-display text-xl tracking-tight">
            Summit <span className="grad-text font-semibold">Bank</span>
          </span>
        </div>

        <div className="panel rounded-3xl p-8 sm:p-10 shadow-2xl">
          <h1 className="font-display text-2xl font-semibold mb-1">Create your account</h1>
          <p className="text-sm text-[var(--text-2)] mb-8">Takes less than a minute.</p>

          {error && (
            <div className="mb-4 text-sm text-[var(--danger)] bg-[rgba(251,113,133,0.1)] border border-[rgba(251,113,133,0.25)] rounded-xl px-4 py-3">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-xs text-[var(--text-2)] mb-1.5 block">Full name</label>
              <div className="input-field rounded-xl px-4 py-3">
                <input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Awele Test"
                  className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-2)] mb-1.5 block">Email</label>
              <div className="input-field rounded-xl px-4 py-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-2)] mb-1.5 block">Password</label>
              <div className="input-field rounded-xl px-4 py-3 flex items-center gap-2">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
                />
                <button type="button" onClick={() => setShowPassword((s) => !s)} className="text-[var(--text-3)]">
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <div>
              <label className="text-xs text-[var(--text-2)] mb-1.5 block">Confirm password</label>
              <div className="input-field rounded-xl px-4 py-3">
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat password"
                  className="bg-transparent w-full text-sm outline-none placeholder:text-[var(--text-3)]"
                />
              </div>
            </div>
            <button type="submit" disabled={submitting} className="btn-primary w-full rounded-xl py-3 text-sm font-medium mt-2">
              {submitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--text-2)] mt-6">
            Already have an account?{' '}
            <Link to="/login" className="hover:underline" style={{ color: 'var(--pink-accent)' }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}