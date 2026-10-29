import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { ChevronRight, LogOut, ShieldCheck, X } from 'lucide-react';
import Blobs from './Blobs';

// The phone menu: a full-screen dark page with one tidy list on a white card.
export default function MoreMenuSheet({ items, onClose, isAdmin, onLogout }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  const row = 'flex items-center gap-3.5 px-5 min-h-[48px] text-sm font-medium border-b border-[#e6e1f0] last:border-0 transition active:bg-[#ece8f4]';

  return (
    <div className="no-print fixed inset-0 z-50 bg-[var(--ink)] overflow-y-auto fade-in" role="dialog" aria-modal="true" aria-label="Menu">
      <Blobs name="corner" opacity={0.5} className="fixed" />
      <div className="relative max-w-md mx-auto px-4 pb-28">
        <div className="flex items-center justify-between px-2 pt-5 pb-4">
          <span className="font-display text-2xl font-bold">Menu</span>
          <button onClick={onClose} aria-label="Close menu" className="w-11 h-11 rounded-full bg-[var(--ink-3)] flex items-center justify-center">
            <X size={20} />
          </button>
        </div>

        <nav aria-label="Menu" className="light-zone rounded-[28px] py-1.5 shadow-2xl">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) => `${row} ${isActive ? 'text-[var(--text-1)] bg-[#ece8f4]' : 'text-[var(--text-1)]'}`}
            >
              <span className="w-8 h-8 rounded-[10px] bg-[#e8e2f5] text-[#3b2a66] flex items-center justify-center shrink-0">
                <item.icon size={16} strokeWidth={1.9} />
              </span>
              <span className="flex-1">{item.label}</span>
              <ChevronRight size={16} className="text-[var(--text-3)]" />
            </NavLink>
          ))}
          {isAdmin && (
            <NavLink to="/admin/users" onClick={onClose} className={`${row} text-[#5b3fa8]`}>
              <span className="w-8 h-8 rounded-[10px] bg-[#e8e2f5] flex items-center justify-center shrink-0">
                <ShieldCheck size={16} strokeWidth={1.9} />
              </span>
              <span className="flex-1">Admin console</span>
              <ChevronRight size={16} />
            </NavLink>
          )}
        </nav>

        <button
          onClick={() => {
            onClose();
            onLogout?.();
          }}
          className="mt-4 w-full h-[52px] rounded-full bg-[var(--ink-3)] text-sm font-medium flex items-center justify-center gap-2.5"
        >
          <LogOut size={18} strokeWidth={1.8} /> Log out
        </button>
      </div>
    </div>
  );
}
