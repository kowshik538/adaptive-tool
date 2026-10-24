import React, { useEffect, useState } from 'react';
import { 
  History, Filter, RefreshCw, CheckCircle2, XCircle, 
  AlertTriangle, Shield, Eye, Clock, Search 
} from 'lucide-react';
import { api } from '../services/api';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [decisionFilter, setDecisionFilter] = useState("");
  const [toolFilter, setToolFilter] = useState("");
  const [expandedLogId, setExpandedLogId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logList, auditStats] = await Promise.all([
        api.getAuditLogs(decisionFilter, toolFilter, 100),
        api.getAuditStats()
      ]);
      setLogs(logList);
      setStats(auditStats);
    } catch (err) {
      console.error("Failed to load audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [decisionFilter, toolFilter]);

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <History className="w-6 h-6 text-sky-400" />
            <span>Tamper-Evident Audit Logs</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete chronological record of all tool attempts, policy enforcement decisions, reason codes, and sanitized inputs.
          </p>
        </div>

        <button
          onClick={loadData}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span>Refresh Logs</span>
        </button>
      </div>

      {/* KPI Counters */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <span className="text-[11px] text-slate-400 block">Total Invocations Logged</span>
            <span className="text-2xl font-bold text-white">{stats.total_calls_logged}</span>
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <span className="text-[11px] text-slate-400 block">Calls Allowed</span>
            <span className="text-2xl font-bold text-emerald-400">{stats.allowed_calls}</span>
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <span className="text-[11px] text-slate-400 block">Unauthorized Calls Denied</span>
            <span className="text-2xl font-bold text-red-400">{stats.denied_calls}</span>
          </div>
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4">
            <span className="text-[11px] text-slate-400 block">Block Ratio</span>
            <span className="text-2xl font-bold text-sky-400">{stats.block_ratio_percent}%</span>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="font-semibold text-slate-300">Filters:</span>
        </div>

        {/* Decision Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-slate-400">Decision:</span>
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg p-1.5 text-slate-200"
          >
            <option value="">All Decisions</option>
            <option value="ALLOW">ALLOW</option>
            <option value="DENY">DENY</option>
            <option value="REQUIRE_APPROVAL">REQUIRE_APPROVAL</option>
          </select>
        </div>

        {/* Tool Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-slate-400">Tool Name:</span>
          <select
            value={toolFilter}
            onChange={(e) => setToolFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg p-1.5 text-slate-200 font-mono"
          >
            <option value="">All Tools</option>
            <option value="read_file">read_file</option>
            <option value="summarize_document">summarize_document</option>
            <option value="calculate_statistics">calculate_statistics</option>
            <option value="search_knowledge_base">search_knowledge_base</option>
            <option value="query_database">query_database</option>
            <option value="send_email">send_email</option>
            <option value="modify_database">modify_database</option>
            <option value="delete_file">delete_file</option>
            <option value="admin_system_command">admin_system_command</option>
            <option value="export_audit_archive">export_audit_archive</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              <tr>
                <th className="py-3 px-4">Time</th>
                <th className="py-3 px-4">Task ID</th>
                <th className="py-3 px-4">Tool</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4">Reason Code</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Strategy</th>
                <th className="py-3 px-4 text-right">Latency</th>
                <th className="py-3 px-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
              {logs.length > 0 ? (
                logs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  const isAllow = log.policy_decision === "ALLOW";
                  const isDeny = log.policy_decision === "DENY";

                  return (
                    <React.Fragment key={log.id}>
                      <tr className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-4 text-slate-400 whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-2.5 px-4 text-sky-400 whitespace-nowrap">{log.task_id}</td>
                        <td className="py-2.5 px-4 font-bold text-white font-mono">{log.tool_name}()</td>
                        <td className="py-2.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isAllow ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                            isDeny ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}>
                            {log.policy_decision}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-300">{log.reason_code}</td>
                        <td className="py-2.5 px-4 text-slate-400 font-sans">{log.user_role}</td>
                        <td className="py-2.5 px-4 text-slate-400 font-sans">{log.access_strategy}</td>
                        <td className="py-2.5 px-4 text-right text-slate-400">{log.latency_ms} ms</td>
                        <td className="py-2.5 px-4 text-center">
                          <button
                            onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                            className="text-xs text-sky-400 hover:text-sky-300 underline font-sans"
                          >
                            {isExpanded ? "Hide" : "Details"}
                          </button>
                        </td>
                      </tr>

                      {/* Expanded Details Drawer */}
                      {isExpanded && (
                        <tr className="bg-slate-950/90 font-sans">
                          <td colSpan={9} className="p-4 space-y-3">
                            <div>
                              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">
                                Reason Description
                              </span>
                              <p className="text-xs text-slate-200 mt-0.5 font-medium">{log.reason_description}</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1">
                                  Sanitized Arguments (Secrets Redacted)
                                </span>
                                <pre className="p-2.5 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                                  {JSON.stringify(log.sanitized_arguments, null, 2)}
                                </pre>
                              </div>

                              <div>
                                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1">
                                  Execution Outcome / Error
                                </span>
                                <pre className="p-2.5 rounded bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                                  {log.execution_result ? JSON.stringify(log.execution_result, null, 2) : log.error_message || "No execution performed."}
                                </pre>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    {loading ? "Loading audit records..." : "No audit records match the current filters."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
