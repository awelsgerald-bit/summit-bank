import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// The PIN box is a React component; it registers itself here so this file can ask for a PIN
// without every page having to know about it.
let pinAsker = null;
export function registerPinAsker(fn) {
  pinAsker = fn;
}

function detailOf(error) {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' ? detail : '';
}

// Sends the same request again with the PIN attached. A wrong PIN asks again (the server counts
// the tries and locks after five); cancelling or a lock ends it.
async function retryWithPin(error, firstMessage) {
  let message = firstMessage;
  for (;;) {
    const pin = await pinAsker(message);
    if (pin == null) {
      error.pinCancelled = true;
      throw error;
    }
    const config = error.config;
    config.headers.set('X-Transaction-Pin', pin);
    try {
      return await api.request(config);
    } catch (retryError) {
      const detail = detailOf(retryError);
      if (retryError.response?.status === 403 && detail.startsWith('PIN_INVALID')) {
        const left = detail.split('|')[1];
        message = `Incorrect PIN. ${left} ${left === '1' ? 'try' : 'tries'} left.`;
        continue;
      }
      throw retryError;
    }
  }
}

// Attach the JWT to every outgoing request, if we have one
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('summit_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If the token is invalid/expired, clear it and bounce to login
    if (error.response?.status === 401) {
      localStorage.removeItem('summit_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    // The action needs the transaction PIN: ask for it, then repeat the request.
    if (
      error.response?.status === 428 &&
      detailOf(error) === 'PIN_REQUIRED' &&
      pinAsker &&
      error.config &&
      !error.config.headers?.get?.('X-Transaction-Pin')
    ) {
      return retryWithPin(error, 'Enter your transaction PIN to continue.');
    }
    return Promise.reject(error);
  }
);

export default api;
