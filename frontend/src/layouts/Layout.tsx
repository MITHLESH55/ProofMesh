import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Activity,
  FolderGit2,
  GitPullRequest,
  LayoutDashboard,
  LogOut,
  Network,
  Settings as SettingsIcon,
  Shield,
  User as UserIcon,
} from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

export const Layout: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [systemReady, setSystemReady] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .getMe()
      .then((data) => setUser(data))
      .catch(() => {
        api.clearToken();
        navigate('/login');
      });

    api
      .getReady()
      .then((ready) => setSystemReady(ready.status === 'ready'))
      .catch(() => setSystemReady(false));
  }, [navigate]);

  const handleLogout = () => {
    api.logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/repositories', label: 'Repositories', icon: FolderGit2 },
    { to: '/changes', label: 'Changes', icon: GitPullRequest },
    { to: '/graph', label: 'Dependency Graph', icon: Network },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div>
          {/* Brand Header */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center text-white font-bold shadow-lg shadow-sky-500/20">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                ProofMesh
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-indigo-950 text-indigo-400 border border-indigo-800/80 rounded">
                  Phase 3
                </span>
              </span>
            </div>
          </div>

          {/* Nav List */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-sky-600/10 text-sky-400 border border-sky-500/20 font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer / User info */}
        <div className="p-4 border-t border-slate-800 space-y-3">
          {/* Health check status indicator */}
          <div className="flex items-center justify-between px-3 py-2 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs">
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-300">System API</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  systemReady === true
                    ? 'bg-emerald-400 shadow-sm shadow-emerald-400'
                    : systemReady === false
                    ? 'bg-rose-500'
                    : 'bg-amber-400'
                }`}
              />
              <span className="font-mono text-[11px] text-slate-400">
                {systemReady === true ? 'Ready' : systemReady === false ? 'Degraded' : 'Checking'}
              </span>
            </div>
          </div>

          {/* User Profile */}
          <div className="flex items-center justify-between px-2 pt-1">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 text-xs font-semibold shrink-0">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
              </div>
              <div className="truncate">
                <p className="text-xs font-medium text-slate-200 truncate">{user?.full_name || 'Loading...'}</p>
                <p className="text-[11px] font-mono text-slate-400 truncate">{user?.role || ''}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-slate-950/70 backdrop-blur sticky top-0 z-10">
          <div>
            <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
              Software Change Assurance & Ingestion
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs font-mono text-indigo-400 px-2 py-1 bg-slate-900 border border-indigo-900/50 rounded">
              v0.3.0-phase3
            </span>
          </div>
        </header>

        <main className="p-8 max-w-7xl w-full mx-auto flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
