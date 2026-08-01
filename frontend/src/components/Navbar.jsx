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
    return localStorage.getItem('theme') || 'light';
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
    <nav className="glass-panel w-64 h-screen sticky top-0 flex flex-col justify-between py-8 px-6 shadow-2xl border-r shrink-0 z-50">
      <div className="space-y-8 flex flex-col">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center space-x-3 px-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-orange-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-orange-500/25 shrink-0">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <span className="font-heading text-lg font-bold tracking-tight text-white">
            Talent<span className="gradient-text">AI</span>
          </span>
        </Link>

        {/* Navigation links */}
        <div className="flex flex-col space-y-2">
          <Link
            to="/dashboard"
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all ${
              isActive('/dashboard')
                ? 'bg-gradient-to-r from-orange-500/20 to-indigo-500/10 text-orange-600 border border-orange-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>
          <Link
            to="/jobs"
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all ${
              isActive('/jobs')
                ? 'bg-gradient-to-r from-orange-500/20 to-indigo-500/10 text-orange-600 border border-orange-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Jobs</span>
          </Link>
          <Link
            to="/analytics"
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all ${
              isActive('/analytics')
                ? 'bg-gradient-to-r from-orange-500/20 to-indigo-500/10 text-orange-600 border border-orange-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </Link>
          <Link
            to="/workforce"
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all ${
              isActive('/workforce')
                ? 'bg-gradient-to-r from-orange-500/20 to-indigo-500/10 text-orange-600 border border-orange-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Workforce</span>
          </Link>
          {user.role === 'admin' && (
            <Link
              to="/settings"
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase transition-all ${
                isActive('/settings')
                  ? 'bg-gradient-to-r from-orange-500/20 to-indigo-500/10 text-orange-600 border border-orange-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Settings</span>
            </Link>
          )}
        </div>
      </div>

      {/* Footer controls & Logout */}
      <div className="flex flex-col space-y-4">
        {/* Toggle Theme */}
        <button
          onClick={toggleTheme}
          className="flex items-center justify-between w-full px-4 py-2.5 rounded-xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800 text-xs text-slate-400 hover:text-white transition-all"
        >
          <span className="font-semibold uppercase tracking-wider">Appearance</span>
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>

        {/* Logout */}
        <button
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="flex items-center space-x-3 px-4 py-3 rounded-xl text-xs font-semibold tracking-wide uppercase text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition-all w-full text-left"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  );
}
