import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BrainCircuit, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, login, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 text-indigo-600 font-bold text-2xl tracking-tight no-underline mb-3">
            <BrainCircuit size={32} />
            <span className="text-slate-900">Smart<span className="text-indigo-600">Interview</span></span>
          </Link>
          <p className="text-sm text-slate-500 font-medium">Welcome back! Please enter your details.</p>
        </div>

        {isAuthenticated && (
          <div className="mb-6 p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-xs text-slate-700 shadow-sm">
            <div className="font-semibold text-slate-900 mb-1">Active Session Detected</div>
            <div className="mb-2">Currently logged in as <strong>{user?.name}</strong> ({user?.email}). Logging in will switch to the new user.</div>
            <div className="flex gap-3 pt-1 border-t border-indigo-100">
              <Link to="/dashboard" className="font-semibold text-indigo-600 hover:text-indigo-800 no-underline">
                Go to Dashboard →
              </Link>
              <button
                type="button"
                onClick={logout}
                className="font-semibold text-red-600 hover:text-red-700 bg-transparent border-none cursor-pointer p-0"
              >
                Log out
              </button>
            </div>
          </div>
        )}

        <div className="card shadow-md p-8">
          {error && <div className="error-message mb-5 bg-red-50 text-red-700 border-red-200">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label" htmlFor="email">Email</label>
              <input id="email" type="email" className="input" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" placeholder="you@example.com" />
            </div>
            <div>
              <label className="label" htmlFor="password">Password</label>
              <div className="relative">
                <input id="password" type={showPw ? 'text' : 'password'} className="input pr-10" value={password} onChange={e => setPassword(e.target.value)} required autoComplete="current-password" placeholder="••••••••" />
                <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer bg-transparent border-none" onClick={() => setShowPw(!showPw)}>
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
            
            <div className="pt-2">
              <button type="submit" className="btn btn-primary w-full py-2.5 text-base" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </div>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 mt-6 font-medium">
          Don't have an account?{' '}
          <Link to="/register" className="text-indigo-600 font-semibold no-underline hover:text-indigo-500 transition-colors">Create one</Link>
        </p>
      </div>
    </div>
  );
}
