import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, Briefcase, Users, BarChart3, TrendingUp, LogOut, Shield, Sun, Moon } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize theme from localStorage or system preference
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'light') {
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.classList.add('dark');
      root.classList.remove('light');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  if (!user) return null;

  const isActive = (path) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <nav className="glass-panel sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-2xl">
      <div className="flex items-center space-x-8">
        <Link to="/dashboard" className="flex items-center space-x-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <span className="font-heading text-xl font-bold tracking-tight text-white dark:text-white">
            Talent<span className="gradient-text">AI</span> Copilot
          </span>
        </Link>

        <div className="hidden md:flex items-center space-x-1">
          <Link
            to="/dashboard"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
              isActive('/dashboard')
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Candidate Dashboard</span>
          </Link>
          <Link
            to="/jobs"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
              isActive('/jobs')
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Job Openings</span>
          </Link>
          <Link
            to="/analytics"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
              isActive('/analytics')
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>HR Analytics</span>
          </Link>
          <Link
            to="/workforce"
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
              isActive('/workforce')
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Workforce</span>
          </Link>
          {user.role === 'admin' && (
            <Link
              to="/settings"
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/settings')
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Settings</span>
            </Link>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Dark/Light mode toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
        >
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>

        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs font-semibold text-slate-300">
            {user.company?.name || user.full_name || 'Tenant Admin'}
          </span>
          <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
            {user.role}
          </span>
        </div>

        <button
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
          title="Logout"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </nav>
  );
}
