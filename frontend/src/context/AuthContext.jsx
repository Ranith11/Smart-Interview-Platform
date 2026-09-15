import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Clean up any legacy localStorage tokens so stale logins from previous sessions do not leak
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch {
      // ignore
    }

    const token = sessionStorage.getItem('token');
    const savedUser = sessionStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        // Verify token is still valid
        api.get('/auth/me').then(res => {
          setUser(res.data);
          sessionStorage.setItem('user', JSON.stringify(res.data));
        }).catch(() => {
          sessionStorage.removeItem('token');
          sessionStorage.removeItem('user');
          setUser(null);
        });
      } catch {
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    sessionStorage.setItem('token', res.data.access_token);
    sessionStorage.setItem('user', JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data;
  };

  const register = async (name, email, password, confirmPassword) => {
    const res = await api.post('/auth/register', {
      name,
      email,
      password,
      confirm_password: confirmPassword,
    });
    sessionStorage.setItem('token', res.data.access_token);
    sessionStorage.setItem('user', JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    try {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    } catch {
      // ignore
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
