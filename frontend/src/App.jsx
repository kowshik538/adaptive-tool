import React, { useState } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import PlaygroundPage from './pages/PlaygroundPage';
import ToolRegistryPage from './pages/ToolRegistryPage';
import ExperimentLabPage from './pages/ExperimentLabPage';
import SecurityTestingPage from './pages/SecurityTestingPage';
import AuditLogsPage from './pages/AuditLogsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentUser, setCurrentUser] = useState({
    username: 'researcher',
    role: 'Researcher',
    email: 'researcher@security.lab'
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500/30 selection:text-sky-200">
      
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentUser={currentUser}
        setCurrentUser={setCurrentUser}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardPage setActiveTab={setActiveTab} currentUser={currentUser} />
        )}
        {activeTab === 'playground' && (
          <PlaygroundPage currentUser={currentUser} />
        )}
        {activeTab === 'tools' && (
          <ToolRegistryPage currentUser={currentUser} />
        )}
        {activeTab === 'experiments' && (
          <ExperimentLabPage currentUser={currentUser} setActiveTab={setActiveTab} />
        )}
        {activeTab === 'security' && (
          <SecurityTestingPage currentUser={currentUser} />
        )}
        {activeTab === 'audit' && (
          <AuditLogsPage />
        )}
        {activeTab === 'reports' && (
          <ReportsPage />
        )}
        {activeTab === 'settings' && (
          <SettingsPage currentUser={currentUser} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <strong>Adaptive Least-Privilege Tool Scoping</strong> — Final Year Research Evaluation Project
          </div>
          <div className="font-mono text-[11px] text-slate-400">
            FastAPI + React + SQLite | Model-Scale Study (3B vs 70B)
          </div>
        </div>
      </footer>

    </div>
  );
}
