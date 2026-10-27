export default function Avatar({ user, size = 32, className = '' }) {
  const initials = user?.full_name
    ? user.full_name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()
    : '';
  const style = { width: size, height: size, fontSize: Math.max(10, Math.round(size / 2.6)) };

  if (user?.avatar) {
    return (
      <img
        src={user.avatar}
        alt={user.full_name || 'Profile photo'}
        style={style}
        className={`rounded-full object-cover shrink-0 ${className}`}
      />
    );
  }
  return (
    <div
      style={style}
      className={`rounded-full grad-primary flex items-center justify-center font-semibold text-[#1B0E3A] shrink-0 ${className}`}
    >
      {initials}
    </div>
  );
}
