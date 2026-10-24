const API_BASE = "http://localhost:8000/api";

let authToken = localStorage.getItem("auth_token") || "";

export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    localStorage.setItem("auth_token", token);
  } else {
    localStorage.removeItem("auth_token");
  }
};

export const getAuthToken = () => authToken;

const authHeaders = () => {
  const headers = { "Content-Type": "application/json" };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
};

async function handleResponse(res) {
  if (!res.ok) {
    let errMessage = `Error ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data && data.detail) errMessage = data.detail;
    } catch (_) {}
    throw new Error(errMessage);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(username, password) {
    const data = await handleResponse(
      await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      })
    );
    setAuthToken(data.access_token);
    return data;
  },

  async getMe() {
    return handleResponse(
      await fetch(`${API_BASE}/auth/me`, {
        headers: authHeaders()
      })
    );
  },

  logout() {
    setAuthToken("");
  },

  // Tools
  async getTools() {
    return handleResponse(await fetch(`${API_BASE}/tools`, { headers: authHeaders() }));
  },

  async updateTool(name, payload) {
    return handleResponse(
      await fetch(`${API_BASE}/tools/${name}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(payload)
      })
    );
  },

  async testTool(name, payload) {
    return handleResponse(
      await fetch(`${API_BASE}/tools/${name}/test`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload || {})
      })
    );
  },

  // Tasks & Playground
  async analyzeTask(taskPrompt) {
    return handleResponse(
      await fetch(`${API_BASE}/tasks/analyze`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ task_prompt: taskPrompt })
      })
    );
  },

  async executeTask(submission) {
    return handleResponse(
      await fetch(`${API_BASE}/tasks/execute`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(submission)
      })
    );
  },

  async approveTask(taskId, toolName, approved, reason) {
    return handleResponse(
      await fetch(`${API_BASE}/tasks/approve`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          task_id: taskId,
          tool_name: toolName,
          approved,
          decision_reason: reason
        })
      })
    );
  },

  // Benchmarks & Experiments
  async getBenchmarks() {
    return handleResponse(await fetch(`${API_BASE}/benchmarks`, { headers: authHeaders() }));
  },

  async runExperiments(payload) {
    return handleResponse(
      await fetch(`${API_BASE}/experiments/run`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload)
      })
    );
  },

  // Security Scenarios
  async getSecurityScenarios() {
    return handleResponse(await fetch(`${API_BASE}/security/scenarios`, { headers: authHeaders() }));
  },

  async runSecurityTest(scenarioId) {
    return handleResponse(
      await fetch(`${API_BASE}/security/test`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ scenario_id: scenarioId })
      })
    );
  },

  // Audit Logs
  async getAuditLogs(decision, toolName, limit = 100) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (decision) params.append("decision", decision);
    if (toolName) params.append("tool_name", toolName);
    return handleResponse(await fetch(`${API_BASE}/audit/logs?${params}`, { headers: authHeaders() }));
  },

  async getAuditStats() {
    return handleResponse(await fetch(`${API_BASE}/audit/stats`, { headers: authHeaders() }));
  },

  // Metrics & Reports
  async getMetricsSummary() {
    return handleResponse(await fetch(`${API_BASE}/metrics/summary`, { headers: authHeaders() }));
  },

  getReportDownloadUrl(fmt = "csv") {
    return `${API_BASE}/reports/export?fmt=${fmt}`;
  },

  // Settings
  async getSettings() {
    return handleResponse(await fetch(`${API_BASE}/settings`, { headers: authHeaders() }));
  },

  async updateSettings(payload) {
    return handleResponse(
      await fetch(`${API_BASE}/settings`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload)
      })
    );
  }
};
