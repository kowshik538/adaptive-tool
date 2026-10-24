import React, { useEffect, useState } from 'react';
import { 
  Wrench, Shield, Play, CheckCircle2, AlertTriangle, 
  Settings, RefreshCw, Lock, Unlock, Database, FileText, 
  Mail, Trash2, Terminal, Search, Check, X
} from 'lucide-react';
import { api } from '../services/api';

const SENSITIVITY_COLORS = {
  LOW: "text-emerald-400 bg-emerald-950/60 border-emerald-800",
  MEDIUM: "text-sky-400 bg-sky-950/60 border-sky-800",
  HIGH: "text-amber-400 bg-amber-950/60 border-amber-800",
  CRITICAL: "text-red-400 bg-red-950/60 border-red-800"
};

export default function ToolRegistryPage({ currentUser }) {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testModal, setTestModal] = useState(null);
  const [testArgs, setTestArgs] = useState("{}");
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [editTool, setEditTool] = useState(null);

  const isAdmin = currentUser.role === "Admin";

  const loadTools = async () => {
    setLoading(true);
    try {
      const data = await api.getTools();
      setTools(data);
    } catch (err) {
      alert("Failed to load tools: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTools();
  }, []);

  const handleToggleTool = async (tool) => {
    if (!isAdmin) {
      alert("Only users with Admin role can modify tool configurations.");
      return;
    }
    try {
      await api.updateTool(tool.name, { is_enabled: !tool.is_enabled });
      loadTools();
    } catch (err) {
      alert("Update failed: " + err.message);
    }
  };

  const openTestModal = (tool) => {
    let defaultPayload = {};
    if (tool.name === "read_file") defaultPayload = { filepath: "financial_report_q3.txt" };
    else if (tool.name === "calculate_statistics") defaultPayload = { numbers: [4250000, 2800000], operation: "margin" };
    else if (tool.name === "search_knowledge_base") defaultPayload = { query: "password", limit: 2 };
    else if (tool.name === "summarize_document") defaultPayload = { text: "Q3 report: revenue $4.25M, expenses $2.8M. Operating margin 34.1%.", max_sentences: 2 };
    else if (tool.name === "query_database") defaultPayload = { table: "employees", query: "SELECT * FROM employees" };
    else if (tool.name === "send_email") defaultPayload = { recipient: "auditor@security.lab", subject: "Compliance Notification", body: "System audit check complete." };
    else if (tool.name === "admin_system_command") defaultPayload = { command: "uptime" };
    else if (tool.name === "delete_file") defaultPayload = { filepath: "temp_cache.log" };
    else if (tool.name === "modify_database") defaultPayload = { table: "employees", action: "insert", data: { name: "Test User" } };
    else defaultPayload = { format: "json" };

    setTestModal(tool);
    setTestArgs(JSON.stringify(defaultPayload, null, 2));
    setTestResult(null);
  };

  const executeDirectTest = async () => {
    if (!testModal) return;
    setTesting(true);
    try {
      const parsed = JSON.parse(testArgs);
      const res = await api.testTool(testModal.name, { arguments: parsed });
      setTestResult(res);
    } catch (err) {
      setTestResult({ error: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveToolEdits = async () => {
    if (!editTool || !isAdmin) return;
    try {
      await api.updateTool(editTool.name, {
        risk_score: editTool.risk_score,
        required_role: editTool.required_role,
        requires_approval_by_default: editTool.requires_approval_by_default,
        is_enabled: editTool.is_enabled
      });
      setEditTool(null);
      loadTools();
    } catch (err) {
      alert("Failed to save changes: " + err.message);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Wrench className="w-6 h-6 text-sky-400" />
            <span>Tool Registry & Policy Metadata</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Maintain tool definitions, schemas, permitted operations, sensitivity classification, risk scoring, and sandboxed test handlers.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {!isAdmin && (
            <span className="text-[11px] text-amber-400 bg-amber-950/40 border border-amber-800/40 px-2.5 py-1 rounded-md">
              Read-Only View ({currentUser.role}). Switch to Admin to modify policies.
            </span>
          )}
          <button
            onClick={loadTools}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {tools.map((tool) => {
          const sensClass = SENSITIVITY_COLORS[tool.sensitivity] || SENSITIVITY_COLORS.LOW;
          return (
            <div
              key={tool.name}
              className={`rounded-xl bg-slate-900 border p-5 flex flex-col justify-between transition-all ${
                tool.is_enabled ? 'border-slate-800 hover:border-slate-700 shadow-sm' : 'border-slate-800/50 opacity-60 bg-slate-950/40'
              }`}
            >
              <div>
                {/* Top Badges */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-1.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${sensClass}`}>
                      {tool.sensitivity}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      Req: {tool.required_role}
                    </span>
                  </div>

                  <div className="flex items-center space-x-1">
                    <span className="text-xs font-mono font-bold text-slate-300">Risk: {tool.risk_score}/10</span>
                  </div>
                </div>

                {/* Name & Category */}
                <div className="mb-2">
                  <h3 className="font-bold text-sm text-white flex items-center space-x-2">
                    <span>{tool.display_name}</span>
                    {!tool.is_enabled && (
                      <span className="text-[10px] text-red-400 font-mono font-normal">(Disabled)</span>
                    )}
                  </h3>
                  <span className="text-[10px] text-sky-400 font-mono block mt-0.5">{tool.name}()</span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {tool.description}
                </p>

                {/* Operations & Approval Details */}
                <div className="space-y-2 border-t border-slate-800/80 pt-3 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Permitted Verbs:</span>
                    <span className="text-slate-300 font-mono">
                      {tool.permitted_operations.join(", ")}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Default Approval:</span>
                    <span className={tool.requires_approval_by_default ? "text-amber-400 font-semibold" : "text-slate-400"}>
                      {tool.requires_approval_by_default ? "Required" : "Automated"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="mt-5 pt-3 border-t border-slate-800 flex items-center justify-between">
                <button
                  onClick={() => openTestModal(tool)}
                  className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 text-xs font-medium border border-sky-500/30 transition"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>Test Tool</span>
                </button>

                {isAdmin && (
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setEditTool({ ...tool })}
                      className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded bg-slate-800 border border-slate-700"
                    >
                      Configure
                    </button>
                    <button
                      onClick={() => handleToggleTool(tool)}
                      className={`text-xs px-2 py-1 rounded font-mono ${
                        tool.is_enabled ? 'text-red-400 hover:bg-red-950/40' : 'text-emerald-400 hover:bg-emerald-950/40'
                      }`}
                    >
                      {tool.is_enabled ? "Disable" : "Enable"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Controlled Test Invocation Modal (Phase 2 Evidence) */}
      {testModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Play className="w-5 h-5 text-sky-400" />
                <h3 className="font-bold text-sm text-white">Controlled Tool Invocation: {testModal.name}()</h3>
              </div>
              <button onClick={() => setTestModal(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Sandboxed Test Arguments (JSON)
              </label>
              <textarea
                rows={4}
                value={testArgs}
                onChange={(e) => setTestArgs(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setTestModal(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={executeDirectTest}
                disabled={testing}
                className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-md shadow-sky-600/30"
              >
                {testing ? "Running..." : "Execute Test"}
              </button>
            </div>

            {testResult && (
              <div className="mt-4 pt-4 border-t border-slate-800">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block mb-1">
                  Sandboxed Execution Result
                </span>
                <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto max-h-48">
                  {JSON.stringify(testResult, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Admin Tool Configuration Modal */}
      {editTool && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-white">Configure {editTool.display_name}</h3>
              <button onClick={() => setEditTool(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Risk Score (1 to 10): {editTool.risk_score}</label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={editTool.risk_score}
                  onChange={(e) => setEditTool({ ...editTool, risk_score: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-semibold">Required User Role</label>
                <select
                  value={editTool.required_role}
                  onChange={(e) => setEditTool({ ...editTool, required_role: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="Admin">Admin</option>
                  <option value="Researcher">Researcher</option>
                  <option value="Tester">Tester</option>
                  <option value="Viewer">Viewer</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="approval_chk"
                  checked={editTool.requires_approval_by_default}
                  onChange={(e) => setEditTool({ ...editTool, requires_approval_by_default: e.target.checked })}
                  className="rounded bg-slate-950 border-slate-800 text-sky-500"
                />
                <label htmlFor="approval_chk" className="text-slate-300 font-medium">Require Admin manual approval before execution</label>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setEditTool(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveToolEdits}
                className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold"
              >
                Save Policy Changes
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
