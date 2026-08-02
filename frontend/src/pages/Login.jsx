import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('admin@company.com');
  const [password, setPassword] = useState('admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    // Clear stale tokens if user lands on login page
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }, []);

  const [retryCount, setRetryCount] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      // Add a 10-second timeout configuration to prevent indefinite hanging
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setRetryCount(prev => prev + 1);
      let errMsg = 'Invalid email or password. Please verify your credentials.';
      
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errMsg = 'Connection timed out. The server or database might be sleeping (Neon Postgres instances spin down after inactivity). Please click Retry.';
      } else if (!err.response) {
        errMsg = 'Network connection failed. Please ensure the backend server is running and try again.';
      } else if (err.response?.status >= 500) {
        errMsg = 'Database wake lag detected. The server is initializing connection pools. Please click the Retry button below.';
      } else if (err.response?.data?.message || err.response?.data?.error?.message) {
        errMsg = err.response.data.message || err.response.data.error.message;
      }
      
      setError(errMsg);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-slate-950">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none" />

      <div className="glass-panel w-full max-w-md p-8 rounded-3xl shadow-2xl relative z-10 border border-slate-800">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-blue-500/30">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="font-heading font-extrabold text-2xl text-white">Welcome Back</h2>
          <p className="text-xs text-slate-400 mt-1">Sign in to your HireRyt Workspace</p>
        </div>

        {error && (
          <div className="mb-5 p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs space-y-2">
            <p className="font-semibold text-center">{error}</p>
            {retryCount > 0 && (
              <div className="pt-2 border-t border-rose-900/40 text-[10px] text-slate-400 space-y-1 text-center">
                <p>💡 Hint: First connection can take up to 10 seconds to spin up Neon Postgres.</p>
                <p>For credentials support, contact <span className="text-blue-400">support@hireryt.com</span></p>
              </div>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Work Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="recruiter@company.com"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-xs hover:opacity-95 disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-lg shadow-blue-500/25"
          >
            <span>{loading ? 'Authenticating...' : retryCount > 0 ? 'Retry Sign In' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-400">
          Need a company account?{' '}
          <Link to="/register" className="font-semibold text-blue-400 hover:underline">
            Register Tenant
          </Link>
        </div>
      </div>
    </div>
  );
}
