import { createContext, useContext, useEffect, useState } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Loads the profile. The login is only thrown away when the server says the token is bad (401);
  // a slow or failed request keeps the token and is retried, so a good password never bounces back.
  async function fetchProfile(retries = 2) {
    for (let attempt = 0; ; attempt++) {
      try {
        const res = await api.get('/account/profile', { timeout: 30000 });
        setUser(res.data);
        return res.data;
      } catch (err) {
        if (err.response?.status === 401) {
          setUser(null);
          localStorage.removeItem('summit_token');
          return null;
        }
        if (attempt >= retries) throw err;
        await new Promise((r) => setTimeout(r, 600 * (attempt + 1)));
      }
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('summit_token');
    if (token) {
      fetchProfile()
        .catch(() => {}) // server unreachable: keep the token, the next request will retry
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(email, password) {
    const res = await api.post('/auth/login', { email: email.trim(), password }, { timeout: 45000 });
    localStorage.setItem('summit_token', res.data.access_token);
    const profile = await fetchProfile().catch(() => null);
    if (!profile) {
      localStorage.removeItem('summit_token');
      const err = new Error('Signed in, but the server was slow to respond. Please tap Sign in again.');
      err.friendly = true;
      throw err;
    }
  }

  // Used by biometric login: the server already issued a token.
  async function loginWithToken(token) {
    localStorage.setItem('summit_token', token);
    const profile = await fetchProfile().catch(() => null);
    if (!profile) {
      localStorage.removeItem('summit_token');
      throw new Error('Signed in, but the server was slow to respond. Please try again.');
    }
  }

  async function register(full_name, email, password, phone_number, referral_code) {
    await api.post('/auth/register', { full_name, email, password, phone_number, referral_code: referral_code || undefined });
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem('summit_token');
    setUser(null);
  }

  const value = { user, loading, login, loginWithToken, register, logout, refreshProfile: fetchProfile };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}