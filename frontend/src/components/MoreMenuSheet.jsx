import { NavLink } from 'react-router-dom';
import { Anchor, ChevronRight, LogOut, ShieldCheck, X } from 'lucide-react';

// The mobile menu: a drawer that slides in from the left, one tidy list row per page.
export default function MoreMenuSheet({ items, onClose, isAdmin, onLogout }) {
  return (
    <div className="no-print fixed inset-0 z-50 flex bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <aside
        className="panel h-full w-[82%] max-w-xs flex flex-col slide-in-left shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        aria-label="Menu"
      >
        <div className="flex items-center justify-between px-5 py-5 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg grad-primary flex items-center justify-center">
              <Anchor size={16} strokeWidth={1.7} />
            </div>
            <span className="font-display text-[15px] tracking-tight">
              Summit <span className="grad-text font-semibold">Bank</span>
            </span>
          </div>
          <button onClick={onClose} className="text-[var(--text-2)]" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-2">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-5 py-3.5 text-sm border-b border-white/5 transition ${
                  isActive ? 'text-[var(--text-1)] bg-[var(--glass)]' : 'text-[var(--text-2)]'
                }`
              }
            >
              <span className="w-8 h-8 rounded-lg grad-primary flex items-center justify-center shrink-0 text-white">
                <item.icon size={15} strokeWidth={1.8} />
              </span>
              <span className="flex-1">{item.label}</span>
              <ChevronRight size={16} className="text-[var(--text-3)]" />
            </NavLink>
          ))}
          {isAdmin && (
            <NavLink
              to="/admin/users"
              onClick={onClose}
              className="flex items-center gap-3.5 px-5 py-3.5 text-sm text-[var(--pink-accent)] border-b border-white/5"
            >
              <span className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 glass">
                <ShieldCheck size={15} strokeWidth={1.8} />
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
          className="flex items-center gap-3.5 px-5 py-4 text-sm text-[var(--text-2)] border-t border-white/5"
        >
          <LogOut size={18} strokeWidth={1.7} /> Log out
        </button>
      </aside>
    </div>
  );
}
