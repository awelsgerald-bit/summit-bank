// The API may answer with { detail: "..." } or { message: "..." }; show whichever it sent.
// The server answers PIN problems with short codes; turn them into sentences.
function friendlyDetail(detail) {
  const [code, extra] = detail.split('|');
  if (code === 'PIN_REQUIRED') return 'Enter your transaction PIN to continue.';
  if (code === 'PIN_NOT_SET') return 'Set a transaction PIN in Settings first.';
  if (code === 'PIN_INVALID') return `Incorrect PIN. ${extra} ${extra === '1' ? 'try' : 'tries'} left.`;
  if (code === 'PIN_LOCKED') return `Too many wrong PIN tries. Try again in about ${extra} minutes.`;
  return detail;
}

export function errorMessage(err, fallback) {
  const data = err?.response?.data;
  if (typeof data?.detail === 'string') return friendlyDetail(data.detail);
  if (typeof data?.message === 'string') return data.message;
  return fallback;
}

export function formatMoney(amount, currency = 'NGN') {
  const n = Number(amount);
  if (currency === 'BTC') return `₿${n.toLocaleString('en-US', { maximumFractionDigits: 8 })}`;
  const symbol = currency === 'NGN' ? '₦' : `${currency} `;
  return symbol + n.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Dates are shown in Nigerian time, matching the statement's date filter.
export function formatDateTime(iso) {
  if (!iso) return '—';
  const value = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  return new Date(value).toLocaleString('en-GB', {
    timeZone: 'Africa/Lagos',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// YYYY-MM-DD for an input[type=date], in Nigerian time.
export function isoDate(date) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Africa/Lagos' }).format(date);
}
