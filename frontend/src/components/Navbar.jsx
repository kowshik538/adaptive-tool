import React, { useState } from 'react';
import { 
  ShieldCheck, LayoutDashboard, Terminal, Wrench, 
  FlaskConical, ShieldAlert, History, BarChart3, Settings, 
  UserCheck, ChevronDown, CheckCircle2 
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, currentUser, setCurrentUser }) {
  const [showRoleMenu, setShowRoleMenu] = useState(false);

  const roles = [
    { name: "Admin", user: "admin", desc: "Full permissions: edit tools, approve actions, modify DB", color: "text-red-400 bg-red-950/40 border-red-800/50" },
    { name: "Researcher", user: "researcher", desc: "Execute benchmarks, view analytics, query database", color: "text-sky-400 bg-sky-950/40 border-sky-800/50" },
    { name: "Tester", user: "tester", desc: "Submit test tasks and evaluate security denials", color: "text-amber-400 bg-amber-950/40 border-amber-800/50" },
    { name: "Viewer", user: "viewer", desc: "Read-only access to dashboards, reports, and logs", color: "text-emerald-400 bg-emerald-950/40 border-emerald-800/50" },
  ];

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'playground', label: 'Playground', icon: Terminal },
    { id: 'tools', label: 'Tool Registry', icon: Wrench },
    { id: 'experiments', label: 'Experiment Lab', icon: FlaskConical },
    { id: 'security', label: 'Security Testing', icon: ShieldAlert },
    { id: 'audit', label: 'Audit Logs', icon: History },
    { id: 'reports', label: 'Results & Reports', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Platform Title */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-md shadow-sky-500/20">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-sky-100 to-sky-400 bg-clip-text text-transparent">
                  Adaptive Tool Scoping
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-400 font-mono border border-sky-500/30">
                  Model-Scale
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Least-Privilege Enforcement for AI Function Calling</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* User Role Switcher */}
          <div className="relative">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className="flex items-center space-x-2.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/80 hover:border-slate-600 text-xs font-medium transition-all"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <div className="text-left">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Role</span>
                <span className="font-semibold text-slate-200">{currentUser.role}</span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
            </button>

            {/* Role Switcher Dropdown */}
            {showRoleMenu && (
              <div className="absolute right-0 mt-2 w-72 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl py-2 z-50">
                <div className="px-3 py-2 border-b border-slate-800">
                  <p className="text-xs font-semibold text-slate-200">Switch Active Test Role</p>
                  <p className="text-[11px] text-slate-400">Evaluate policy boundaries across user tiers</p>
                </div>
                <div className="p-1 space-y-1">
                  {roles.map((r) => {
                    const isSelected = currentUser.role === r.name;
                    return (
                      <button
                        key={r.name}
                        onClick={() => {
                          setCurrentUser({ ...currentUser, role: r.name, username: r.user });
                          setShowRoleMenu(false);
                        }}
                        className={`w-full text-left p-2 rounded-lg text-xs transition-colors flex items-start justify-between ${
                          isSelected ? 'bg-slate-800 border border-slate-700' : 'hover:bg-slate-800/50'
                        }`}
                      >
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${r.color}`}>
                              {r.name}
                            </span>
                            <span className="text-slate-300 font-mono text-[11px]">@{r.user}</span>
                          </div>
                          <p className="text-[10px] text-slate-400 mt-1 leading-tight">{r.desc}</p>
                        </div>
                        {isSelected && <CheckCircle2 className="w-4 h-4 text-sky-400 shrink-0 mt-1" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
      
      {/* Mobile/Tablet Tab Bar */}
      <div className="lg:hidden flex overflow-x-auto px-4 py-2 border-t border-slate-800/80 space-x-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap ${
                isActive ? 'bg-sky-500/20 text-sky-400' : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
