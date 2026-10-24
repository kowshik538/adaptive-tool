import React, { useEffect, useState } from 'react';
import { 
  Settings, Shield, Sliders, Users, Database, 
  CheckCircle2, RefreshCw, Key, Server, Lock 
} from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage({ currentUser }) {
  const [policySettings, setPolicySettings] = useState({
    max_risk_threshold: 7,
    enforce_relevance_check: true,
    block_destructive_ops: true,
    block_exfiltration_tools: true
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const isAdmin = currentUser.role === "Admin";

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await api.getSettings();
        setPolicySettings({
          max_risk_threshold: data.max_risk_threshold || 7,
          enforce_relevance_check: data.enforce_relevance_check ?? true,
          block_destructive_ops: data.block_destructive_ops ?? true,
          block_exfiltration_tools: data.block_exfiltration_tools ?? true
        });
      } catch (err) {
        console.error("Failed to load settings", err);
      }
    }
    loadSettings();
  }, []);

  const handleSaveSettings = async () => {
    if (!isAdmin) {
      alert("Only users with Admin role can modify system security parameters.");
      return;
    }
    setSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateSettings(policySettings);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert("Save failed: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-5xl mx-auto">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
          <Settings className="w-6 h-6 text-sky-400" />
          <span>System Security Policies & Role Administration</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure security policy enforcement boundaries, adjust risk tolerance thresholds, and manage role-based authorization tiers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Left Col: Security Engine Policy Parameters */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-sky-400" />
              <h3 className="font-bold text-sm text-white">Dynamic Policy Engine Thresholds</h3>
            </div>
            {!isAdmin && (
              <span className="text-[10px] text-amber-400 font-mono">View Only (Admin required)</span>
            )}
          </div>

          <div className="space-y-4 text-xs">
            {/* Risk Threshold Slider */}
            <div>
              <div className="flex justify-between mb-1.5">
                <span className="text-slate-300 font-semibold">Max Risk Score Threshold:</span>
                <span className="font-mono font-bold text-sky-400">{policySettings.max_risk_threshold} / 10</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                disabled={!isAdmin}
                value={policySettings.max_risk_threshold}
                onChange={(e) => setPolicySettings({ ...policySettings, max_risk_threshold: parseInt(e.target.value) })}
                className="w-full accent-sky-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Tools with risk rating exceeding this threshold will require explicit Admin privilege or be denied.
              </p>
            </div>

            {/* Relevance Check Toggle */}
            <div className="flex items-start justify-between pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-200 font-semibold block">Task Semantic Relevance Check</span>
                <span className="text-[10px] text-slate-400">Enforce zero-trust candidate capability matching per task.</span>
              </div>
              <input
                type="checkbox"
                disabled={!isAdmin}
                checked={policySettings.enforce_relevance_check}
                onChange={(e) => setPolicySettings({ ...policySettings, enforce_relevance_check: e.target.checked })}
                className="mt-1 rounded bg-slate-950 border-slate-700 text-sky-500"
              />
            </div>

            {/* Destructive Ops Blocker */}
            <div className="flex items-start justify-between pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-200 font-semibold block">Block Destructive Ops for Non-Admins</span>
                <span className="text-[10px] text-slate-400">Strictly disallows file deletion and database drops for Researcher/Tester/Viewer.</span>
              </div>
              <input
                type="checkbox"
                disabled={!isAdmin}
                checked={policySettings.block_destructive_ops}
                onChange={(e) => setPolicySettings({ ...policySettings, block_destructive_ops: e.target.checked })}
                className="mt-1 rounded bg-slate-950 border-slate-700 text-sky-500"
              />
            </div>

            {/* Exfiltration Blocker */}
            <div className="flex items-start justify-between pt-2 border-t border-slate-800">
              <div>
                <span className="text-slate-200 font-semibold block">Prevent Outbound Data Exfiltration</span>
                <span className="text-[10px] text-slate-400">Holds or strips outbound communication tools when credentials or confidential data are detected.</span>
              </div>
              <input
                type="checkbox"
                disabled={!isAdmin}
                checked={policySettings.block_exfiltration_tools}
                onChange={(e) => setPolicySettings({ ...policySettings, block_exfiltration_tools: e.target.checked })}
                className="mt-1 rounded bg-slate-950 border-slate-700 text-sky-500"
              />
            </div>

            {isAdmin && (
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <button
                  onClick={handleSaveSettings}
                  disabled={saving}
                  className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/30 transition"
                >
                  {saving ? "Saving Changes..." : "Save Policy Configuration"}
                </button>
                {saveSuccess && (
                  <span className="text-emerald-400 flex items-center space-x-1 text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Saved!</span>
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: RBAC Roles Directory */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
            <Users className="w-5 h-5 text-indigo-400" />
            <h3 className="font-bold text-sm text-white">Role-Based Access Control (RBAC) Matrix</h3>
          </div>

          <div className="space-y-3 text-xs">
            {[
              {
                role: "Admin",
                desc: "Privileged administrator. Authorized for all tools, policy threshold tuning, and destructive overrides.",
                perms: ["Full Tool Catalogue", "Modify Security Policies", "Approve Held Calls", "Root System Commands"],
                badge: "bg-red-500/20 text-red-400 border-red-500/30"
              },
              {
                role: "Researcher",
                desc: "Research analyst. Authorized to run batch benchmarks, database queries, and metric export reports.",
                perms: ["Run Experiment Lab", "Execute Benchmark Matrix", "Query Database", "Export Reports"],
                badge: "bg-sky-500/20 text-sky-400 border-sky-500/30"
              },
              {
                role: "Tester / Evaluator",
                desc: "Quality & security evaluator. Submits controlled adversarial test payloads to verify policy denials.",
                perms: ["Submit Playground Tasks", "Run Adversarial Tests", "Inspect Denials"],
                badge: "bg-amber-500/20 text-amber-400 border-amber-500/30"
              },
              {
                role: "Viewer",
                desc: "Auditor and observer. Read-only access to dashboards, metrics, and logs. Blocked from writes.",
                perms: ["View Analytics Dashboards", "Read Audit Logs", "Read Public Docs"],
                badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
              }
            ].map((r) => (
              <div key={r.role} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${r.badge}`}>
                    {r.role}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">{r.desc}</p>
                <div className="flex flex-wrap gap-1 pt-1">
                  {r.perms.map((p, i) => (
                    <span key={i} className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">
                      ✓ {p}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* System Environment Status */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-3">
        <h3 className="font-bold text-sm text-white flex items-center space-x-2">
          <Server className="w-4 h-4 text-emerald-400" />
          <span>Runtime Environment & Storage</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Database Engine</span>
            <span className="text-slate-200 font-bold">SQLite 3 (WAL Mode)</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Backend Framework</span>
            <span className="text-slate-200 font-bold">FastAPI + Uvicorn</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Cognitive Agent Runtime</span>
            <span className="text-emerald-400 font-bold">Dual: Local Sim + Ollama Bridge</span>
          </div>
        </div>
      </div>

    </div>
  );
}
