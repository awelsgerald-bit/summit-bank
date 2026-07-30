import { Link } from 'react-router-dom';

export default function QuickAction({ to, label, icon }) {
  return (
    <Link
      to={to}
      className="hover-lift glass rounded-2xl p-4 flex flex-col items-center gap-2.5 text-center"
    >
      <div className="w-10 h-10 rounded-xl grad-primary flex items-center justify-center">{icon}</div>
      <span className="text-xs text-[var(--text-2)]">{label}</span>
    </Link>
  );
}