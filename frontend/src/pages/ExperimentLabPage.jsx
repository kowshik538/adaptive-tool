import React, { useEffect, useState } from 'react';
import { 
  FlaskConical, Play, CheckCircle2, AlertTriangle, 
  Layers, Cpu, BarChart2, Check, RefreshCw, Filter 
} from 'lucide-react';
import { api } from '../services/api';

export default function ExperimentLabPage({ currentUser, setActiveTab }) {
  const [benchmarks, setBenchmarks] = useState([]);
  const [selectedBenchmarkIds, setSelectedBenchmarkIds] = useState([]);
  const [strategies, setStrategies] = useState(["Full Access", "Moderate Access", "Least-Privilege"]);
  const [models, setModels] = useState(["Small Model (3B)", "Large Model (70B)"]);
  const [repetitions, setRepetitions] = useState(1);

  const [running, setRunning] = useState(false);
  const [runProgress, setRunProgress] = useState(null);
  const [matrixData, setMatrixData] = useState([]);
  const [categoryFilter, setCategoryFilter] = useState("ALL");

  const isResearcherOrAdmin = ["Admin", "Researcher"].includes(currentUser.role);

  const loadData = async () => {
    try {
      const [bList, summary] = await Promise.all([
        api.getBenchmarks(),
        api.getMetricsSummary()
      ]);
      setBenchmarks(bList);
      // Select first 4 benchmarks by default
      if (selectedBenchmarkIds.length === 0) {
        setSelectedBenchmarkIds(bList.slice(0, 4).map(b => b.id));
      }
      setMatrixData(summary.comparison_matrix || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleBenchmark = (id) => {
    if (selectedBenchmarkIds.includes(id)) {
      setSelectedBenchmarkIds(selectedBenchmarkIds.filter(x => x !== id));
    } else {
      setSelectedBenchmarkIds([...selectedBenchmarkIds, id]);
    }
  };

  const handleSelectAll = () => {
    setSelectedBenchmarkIds(benchmarks.map(b => b.id));
  };

  const handleClearAll = () => {
    setSelectedBenchmarkIds([]);
  };

  const handleRunBatch = async () => {
    if (!isResearcherOrAdmin) {
      alert("Role requires Researcher or Admin privileges to trigger benchmark experiment runs.");
      return;
    }
    if (selectedBenchmarkIds.length === 0) {
      alert("Please select at least one benchmark task.");
      return;
    }

    setRunning(true);
    setRunProgress("Initializing controlled benchmark matrix...");

    try {
      const res = await api.runExperiments({
        benchmark_ids: selectedBenchmarkIds,
        strategies: strategies,
        models: models,
        repetitions: repetitions
      });
      setRunProgress(`Completed ${res.total_executions} runs across configurations!`);
      // Reload summary matrix
      const updatedSummary = await api.getMetricsSummary();
      setMatrixData(updatedSummary.comparison_matrix || []);
    } catch (err) {
      alert("Experiment failed: " + err.message);
    } finally {
      setRunning(false);
    }
  };

  const categories = ["ALL", ...new Set(benchmarks.map(b => b.category))];
  const filteredBenchmarks = categoryFilter === "ALL" 
    ? benchmarks 
    : benchmarks.filter(b => b.category === categoryFilter);

  return (
    <div className="space-y-6 animate-fadeIn max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <FlaskConical className="w-6 h-6 text-sky-400" />
            <span>Experiment Lab & Benchmark Suite</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Conduct reproducible evaluations comparing Full Access vs. Moderate vs. Least-Privilege across Small (3B) and Large (70B) models.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('reports')}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 transition"
        >
          <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>View Detailed Statistical Charts</span>
        </button>
      </div>

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Benchmark Task Selection */}
        <div className="lg:col-span-2 rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h3 className="font-bold text-sm text-white">Select Benchmark Tasks ({selectedBenchmarkIds.length}/{benchmarks.length})</h3>
              <p className="text-[11px] text-slate-400">Covers 6 distinct capability and adversarial categories</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <button onClick={handleSelectAll} className="text-xs text-sky-400 hover:underline">Select All</button>
              <span className="text-slate-600">|</span>
              <button onClick={handleClearAll} className="text-xs text-slate-400 hover:underline">Clear</button>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {categories.map((c) => (
              <button
                key={c}
                onClick={() => setCategoryFilter(c)}
                className={`px-2.5 py-1 rounded-md text-[11px] border transition ${
                  categoryFilter === c
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/50 font-semibold'
                    : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {c}
              </button>
            ))}
          </div>

          {/* Benchmark Task List */}
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {filteredBenchmarks.map((b) => {
              const isChecked = selectedBenchmarkIds.includes(b.id);
              return (
                <div
                  key={b.id}
                  onClick={() => handleToggleBenchmark(b.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition text-xs flex items-start space-x-3 ${
                    isChecked
                      ? 'bg-slate-800/80 border-sky-500/40 text-slate-200'
                      : 'bg-slate-950/40 border-slate-800/70 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    className="mt-0.5 rounded bg-slate-950 border-slate-700 text-sky-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-sky-400 text-[11px]">{b.id}</span>
                      <span className="font-semibold text-white">{b.title}</span>
                      {b.is_adversarial && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] bg-red-950 text-red-400 border border-red-800 font-bold">
                          ADVERSARIAL
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-300 line-clamp-1">{b.task_prompt}</p>
                    <div className="mt-1 flex items-center space-x-3 text-[10px] text-slate-500">
                      <span>Category: <strong className="text-slate-400">{b.category}</strong></span>
                      <span>Expected: <strong className="text-slate-400 font-mono">{b.expected_tools.join(", ") || "None"}</strong></span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Matrix Parameters */}
        <div className="rounded-xl bg-slate-900 border border-slate-800 p-5 space-y-5">
          <h3 className="font-bold text-sm text-white border-b border-slate-800 pb-2">
            Experimental Matrix Configuration
          </h3>

          {/* Access Strategies */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-2">Access Strategies to Evaluate</label>
            <div className="space-y-1.5 text-xs">
              {["Full Access", "Moderate Access", "Least-Privilege"].map((s) => (
                <label key={s} className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strategies.includes(s)}
                    onChange={(e) => {
                      if (e.target.checked) setStrategies([...strategies, s]);
                      else setStrategies(strategies.filter(x => x !== s));
                    }}
                    className="rounded bg-slate-950 border-slate-700 text-sky-500"
                  />
                  <span>{s}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Model Scales */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-2">Model Scales to Evaluate</label>
            <div className="space-y-1.5 text-xs">
              {["Small Model (3B)", "Large Model (70B)"].map((m) => (
                <label key={m} className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={models.includes(m)}
                    onChange={(e) => {
                      if (e.target.checked) setModels([...models, m]);
                      else setModels(models.filter(x => x !== m));
                    }}
                    className="rounded bg-slate-950 border-slate-700 text-sky-500"
                  />
                  <span>{m}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Total Calculations summary */}
          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1 text-xs font-mono text-slate-400">
            <div>Benchmarks: <strong className="text-slate-200">{selectedBenchmarkIds.length}</strong></div>
            <div>Strategies: <strong className="text-slate-200">{strategies.length}</strong></div>
            <div>Models: <strong className="text-slate-200">{models.length}</strong></div>
            <div className="border-t border-slate-800 pt-1 text-sky-400">
              Total Runs: {selectedBenchmarkIds.length * strategies.length * models.length * repetitions}
            </div>
          </div>

          {/* Run Batch Button */}
          <button
            onClick={handleRunBatch}
            disabled={running || selectedBenchmarkIds.length === 0}
            className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white text-xs font-bold transition shadow-lg shadow-sky-600/30 flex items-center justify-center space-x-2"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{running ? "Executing Benchmark Matrix..." : "Run Controlled Experiment"}</span>
          </button>

          {runProgress && (
            <p className="text-[11px] text-emerald-400 text-center font-mono animate-fadeIn">
              {runProgress}
            </p>
          )}
        </div>

      </div>

      {/* Comparative Evaluation Matrix Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="font-bold text-sm text-white">Strategy × Model Scale Comparative Findings</h3>
            <p className="text-xs text-slate-400">Computed strictly from database task execution logs</p>
          </div>
          <span className="text-xs font-mono text-slate-400">{matrixData.length} matrix slices</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              <tr>
                <th className="py-2.5 px-3">Access Strategy</th>
                <th className="py-2.5 px-3">Model Scale</th>
                <th className="py-2.5 px-3 text-right">Runs</th>
                <th className="py-2.5 px-3 text-right">Success Rate</th>
                <th className="py-2.5 px-3 text-right">Tool Accuracy</th>
                <th className="py-2.5 px-3 text-right">Unnecessary Calls</th>
                <th className="py-2.5 px-3 text-right">Security Exposure</th>
                <th className="py-2.5 px-3 text-right">Attack Success</th>
                <th className="py-2.5 px-3 text-right">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono text-xs">
              {matrixData.map((row, i) => (
                <tr key={i} className="hover:bg-slate-800/40 transition">
                  <td className="py-2.5 px-3 font-semibold text-white font-sans">
                    <span className={`px-2 py-0.5 rounded text-[11px] ${
                      row.strategy === 'Least-Privilege' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' :
                      row.strategy === 'Moderate Access' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                      'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {row.strategy}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-300 font-sans">{row.model}</td>
                  <td className="py-2.5 px-3 text-right text-slate-400">{row.count}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400">{row.task_success}%</td>
                  <td className="py-2.5 px-3 text-right text-sky-400">{row.tool_accuracy}%</td>
                  <td className="py-2.5 px-3 text-right text-slate-300">{row.unnecessary_calls}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-slate-200">{row.security_exposure}</td>
                  <td className="py-2.5 px-3 text-right font-bold">
                    <span className={row.attack_success_rate > 0 ? "text-red-400" : "text-emerald-400"}>
                      {row.attack_success_rate}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-400">{row.latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
