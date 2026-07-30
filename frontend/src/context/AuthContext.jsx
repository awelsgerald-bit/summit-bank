import { createContext, useContext, useEffect, useState } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  async function fetchProfile() {
    try {
      const res = await api.get('/account/profile');
      setUser(res.data);
    } catch {
      setUser(null);
      localStorage.removeItem('summit_token');
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('summit_token');
    if (token) {
      fetchProfile().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(email, password) {
    const res = await api.post('/auth/login', { email, password });
    localStorage.setItem('summit_token', res.data.access_token);
    await fetchProfile();
  }

  async function register(full_name, email, password) {
    await api.post('/auth/register', { full_name, email, password });
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem('summit_token');
    setUser(null);
  }

  const value = { user, loading, login, register, logout, refreshProfile: fetchProfile };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}