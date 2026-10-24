import React, { useEffect, useState } from 'react';
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, Play, CheckCircle2, 
  XCircle, Lock, Unlock, Mail, Trash2, Database, Terminal, ArrowRight 
} from 'lucide-react';
import { api } from '../services/api';

export default function SecurityTestingPage({ currentUser }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [testing, setTesting] = useState(false);
  const [comparisonResult, setComparisonResult] = useState(null);

  useEffect(() => {
    async function loadScenarios() {
      try {
        const sc = await api.getSecurityScenarios();
        setScenarios(sc);
        if (sc.length > 0) setSelectedScenario(sc[0]);
      } catch (err) {
        console.error("Failed to load scenarios", err);
      }
    }
    loadScenarios();
  }, []);

  const handleRunSecurityTest = async () => {
    if (!selectedScenario) return;
    setTesting(true);
    setComparisonResult(null);
    try {
      const res = await api.runSecurityTest(selectedScenario.id);
      setComparisonResult(res.comparison);
    } catch (err) {
      alert("Security test execution failed: " + err.message);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
          <ShieldAlert className="w-6 h-6 text-red-400" />
          <span>Controlled Adversarial Security Testing</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Execute controlled prompt injection and privilege escalation vectors. Compare side-by-side security resilience across Full Access, Moderate Access, and Adaptive Least-Privilege.
        </p>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {scenarios.map((sc) => {
          const isSelected = selectedScenario?.id === sc.id;
          return (
            <div
              key={sc.id}
              onClick={() => {
                setSelectedScenario(sc);
                setComparisonResult(null);
              }}
              className={`p-4 rounded-xl border cursor-pointer transition text-xs flex flex-col justify-between ${
                isSelected
                  ? 'bg-red-950/20 border-red-500/60 shadow-lg shadow-red-900/10'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-red-400 text-[11px]">{sc.id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-red-950 text-red-300 border border-red-800 font-bold uppercase">
                    {sc.adversarial_payload_type || "PROMPT_INJECTION"}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-white mb-1">{sc.title}</h3>
                <p className="text-xs text-slate-300 font-mono bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 mb-3">
                  "{sc.task_prompt}"
                </p>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span>Forbidden tools: <strong className="text-red-400 font-mono">{sc.forbidden_tools.join(", ")}</strong></span>
                <span className={isSelected ? "text-red-400 font-bold" : "text-slate-500"}>
                  {isSelected ? "Selected" : "Click to select"}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Run Action */}
      {selectedScenario && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-white">
              Execute 3-Way Comparative Attack Test
            </h3>
            <p className="text-xs text-slate-400">
              Simultaneously dispatches the malicious prompt through Strategy A, Strategy B, and Strategy C.
            </p>
          </div>

          <button
            onClick={handleRunSecurityTest}
            disabled={testing}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-lg shadow-red-600/30 transition"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{testing ? "Testing Security Boundaries..." : "Run Side-by-Side Adversarial Test"}</span>
          </button>
        </div>
      )}

      {/* Side-by-Side Comparative Results */}
      {comparisonResult && (
        <div className="space-y-4 animate-fadeIn">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <span>Comparative Defense Posture Results</span>
            <span className="text-xs text-slate-400 font-normal">Scenario: {selectedScenario?.id}</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {["Full Access", "Moderate Access", "Least-Privilege"].map((strat) => {
              const res = comparisonResult[strat];
              if (!res) return null;
              const isLeastPrivilege = strat === "Least-Privilege";
              const attackSucceeded = res.attack_succeeded;

              return (
                <div
                  key={strat}
                  className={`rounded-xl border p-5 flex flex-col justify-between ${
                    attackSucceeded
                      ? 'bg-red-950/20 border-red-500/50 glow-danger'
                      : isLeastPrivilege
                      ? 'bg-emerald-950/20 border-emerald-500/50 glow-success'
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-bold text-xs text-white">{strat}</span>
                      {attackSucceeded ? (
                        <span className="flex items-center space-x-1 text-red-400 text-xs font-bold">
                          <XCircle className="w-4 h-4" />
                          <span>EXPLOITED</span>
                        </span>
                      ) : (
                        <span className="flex items-center space-x-1 text-emerald-400 text-xs font-bold">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>NEUTRALIZED</span>
                        </span>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="mb-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        attackSucceeded ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white'
                      }`}>
                        {attackSucceeded ? "ATTACK SUCCEEDED" : "ATTACK PREVENTED"}
                      </span>
                    </div>

                    {/* Scoping Explanation */}
                    <div className="space-y-2 text-xs border-t border-slate-800/80 pt-3">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Scoped Allow-List Exposed:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {res.scoped_allow_list.map((t) => (
                            <span key={t} className={`px-1.5 py-0.5 rounded font-mono text-[10px] ${
                              ["send_email", "delete_file", "admin_system_command", "modify_database"].includes(t)
                                ? 'bg-red-900/60 text-red-300 font-bold border border-red-700'
                                : 'bg-slate-800 text-slate-300'
                            }`}>
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="pt-2">
                        <span className="text-slate-400 block text-[10px]">Audit Decisions:</span>
                        <div className="space-y-1 mt-1">
                          {res.audit_events.map((evt, idx) => (
                            <div key={idx} className="p-2 rounded bg-slate-950 font-mono text-[10px]">
                              <span className={evt.decision === 'ALLOW' ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'}>
                                [{evt.decision}]
                              </span>{" "}
                              <span className="text-slate-200">{evt.tool_name}()</span>
                              <div className="text-slate-400 text-[9px] mt-0.5">{evt.reason_code}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Summary note */}
                  <div className="mt-4 pt-3 border-t border-slate-800 text-[11px]">
                    {isLeastPrivilege ? (
                      <p className="text-emerald-400 font-medium">
                        🛡️ Scoping engine analyzed the prompt, stripped the adversarial tool from the scope, and blocked unauthorized execution.
                      </p>
                    ) : attackSucceeded ? (
                      <p className="text-red-400 font-medium">
                        ⚠️ Tool was exposed to the model runtime. The prompt injection tricked the model into calling it.
                      </p>
                    ) : (
                      <p className="text-slate-400">
                        Attack prevented by static subset rule.
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}
