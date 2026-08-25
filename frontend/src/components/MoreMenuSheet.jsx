import { NavLink } from 'react-router-dom';
import { X } from 'lucide-react';

export default function MoreMenuSheet({ items, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div className="panel rounded-t-3xl w-full max-w-md p-6 pb-8 fade-in">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-display text-base font-medium">More</h3>
          <button onClick={onClose} className="text-[var(--text-2)]">
            <X size={20} />
          </button>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className="glass rounded-2xl p-4 flex flex-col items-center gap-2 text-center"
            >
              <div className="w-9 h-9 rounded-xl grad-primary flex items-center justify-center">
                <item.icon size={16} />
              </div>
              <span className="text-[11px] text-[var(--text-2)]">{item.label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </div>
  );
}