import React from 'react';
import Navbar from './Navbar';
import { Search, Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function DashboardLayout({ children }) {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Left Sidebar */}
      <Navbar />

      {/* Right Side Panel */}
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        {/* Top Header */}
        <header className="glass-panel px-8 py-4 flex items-center justify-between shadow-md border-b shrink-0">
          {/* Top Search bar */}
          <div className="relative max-w-md w-full">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search candidates, jobs, resumes..."
              className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-11 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all"
            />
          </div>

          {/* Top Actions */}
          <div className="flex items-center space-x-6">
            <button className="relative p-2 rounded-xl hover:bg-slate-800/60 text-slate-300 transition-all">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-orange-500 rounded-full"></span>
            </button>

            <div className="flex items-center space-x-3 border-l border-slate-800 pl-6">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-orange-500 to-indigo-500 flex items-center justify-center font-bold text-xs text-white shadow-md">
                {user?.full_name?.charAt(0) || 'A'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-white leading-tight">{user?.full_name || 'Recruiter'}</p>
                <p className="text-[10px] text-slate-400 capitalize">{user?.role || 'admin'}</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
