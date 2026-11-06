#!/usr/bin/env python3
"""
FIN 67110 - Equity Research Desk (Lab 05 Browser Web UI)
A zero-dependency browser application that runs the agent team graph,
displays live node progress, and renders verified reports and marks tables.
"""

import http.server
import json
import os
import re
import socketserver
import sys
import threading
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project imports
import desk_app
import verifier

PORT = 8501
HOST = "127.0.0.1"

# Global state for current execution
RUN_STATE = {
    "status": "idle",  # "idle", "running", "completed", "error"
    "current_node": "",
    "logs": [],
    "last_run_dir": "",
    "result": None,
}


def get_available_runs() -> List[str]:
    """Find saved run folders in workspace."""
    base_dir = Path(__file__).resolve().parent
    folders = []
    # Search local dir and user home dir
    search_paths = [base_dir, Path(r"C:\Users\cashi")]
    for p in search_paths:
        if p.exists():
            for item in p.iterdir():
                if item.is_dir() and (item.name.startswith("COST_") or item.name.startswith("WMT_") or "_" in item.name):
                    if (item / "report.md").exists() or (item / "facts.json").exists():
                        if item.name not in folders:
                            folders.append(item.name)
    return sorted(folders, reverse=True)


def load_run_data(run_folder_name: str) -> Dict[str, Any]:
    """Load report, marks, and node_io from a run folder."""
    base_dir = Path(__file__).resolve().parent
    run_dir = base_dir / run_folder_name
    if not run_dir.exists():
        run_dir = Path(r"C:\Users\cashi") / run_folder_name

    data = {"run_name": run_folder_name, "marks": "", "report": "", "node_io": {}}
    if not run_dir.exists():
        return data

    marks_file = run_dir / "marks.md"
    if marks_file.exists():
        with open(marks_file, "r", encoding="utf-8") as f:
            data["marks"] = f.read()

    verified_report_file = run_dir / "verified_report.md"
    if verified_report_file.exists():
        with open(verified_report_file, "r", encoding="utf-8") as f:
            data["report"] = f.read()
    else:
        report_file = run_dir / "report.md"
        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                data["report"] = f.read()

    io_file = run_dir / "node_io.json"
    if io_file.exists():
        try:
            with open(io_file, "r", encoding="utf-8") as f:
                data["node_io"] = json.load(f)
        except Exception:
            pass

    return data


def run_agent_team_worker(ticker: str, peers: List[str], price: Optional[float]):
    """Background worker executing the 6-node deterministic agent team graph."""
    global RUN_STATE
    RUN_STATE["status"] = "running"
    RUN_STATE["logs"] = [f"Starting Agent Team Graph for ticker: {ticker.upper()}"]
    RUN_STATE["current_node"] = "steps"

    try:
        desk = desk_app.EquityResearchAgentTeam(ticker=ticker, peers=peers, price=price)
        RUN_STATE["logs"].append("Node 1: steps (SEC EDGAR & Facts Calculation)")
        RUN_STATE["current_node"] = "research_analyst"
        
        # Run graph
        verified_file = desk.run_graph()
        work_dir = verified_file.parent

        RUN_STATE["last_run_dir"] = work_dir.name
        RUN_STATE["status"] = "completed"
        RUN_STATE["current_node"] = "completed"
        RUN_STATE["logs"].append(f"Graph completed successfully. Run folder: {work_dir.name}")
        RUN_STATE["result"] = load_run_data(work_dir.name)
    except Exception as e:
        RUN_STATE["status"] = "error"
        RUN_STATE["logs"].append(f"Error during execution: {str(e)}")
        RUN_STATE["current_node"] = "error"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FIN 67110 - Equity Research Agent Team</title>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --accent: #38bdf8;
      --accent-hover: #0ea5e9;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --border: #334155;
      --success: #22c55e;
      --danger: #ef4444;
      --warning: #f59e0b;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 24px; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
    h1 { font-size: 24px; font-weight: 700; color: var(--accent); }
    .subtitle { font-size: 14px; color: var(--text-muted); margin-top: 4px; }
    .grid { display: grid; grid-template-columns: 360px 1fr; gap: 24px; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 20px; margin-bottom: 20px; }
    .card-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }
    label { display: block; font-size: 13px; font-weight: 500; color: var(--text-muted); margin-bottom: 6px; }
    input[type="text"], input[type="number"], select {
      width: 100%; padding: 10px 12px; background: #0f172a; border: 1px solid var(--border);
      border-radius: 6px; color: var(--text); font-size: 14px; margin-bottom: 14px;
    }
    input:focus, select:focus { outline: none; border-color: var(--accent); }
    button {
      width: 100%; padding: 12px; background: var(--accent); color: #0f172a; font-weight: 600;
      font-size: 14px; border: none; border-radius: 6px; cursor: pointer; transition: 0.2s;
    }
    button:hover { background: var(--accent-hover); }
    button.secondary { background: #334155; color: var(--text); margin-top: 10px; }
    button.secondary:hover { background: #475569; }
    .node-steps { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
    .node-step {
      display: flex; align-items: center; gap: 12px; padding: 10px 12px; background: #0f172a;
      border: 1px solid var(--border); border-radius: 6px; font-size: 13px;
    }
    .node-step.active { border-color: var(--accent); background: rgba(56, 189, 248, 0.08); font-weight: 600; }
    .node-step.done { border-color: var(--success); }
    .node-badge { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; background: #334155; color: var(--text); }
    .node-step.active .node-badge { background: var(--accent); color: #0f172a; }
    .node-step.done .node-badge { background: var(--success); color: #0f172a; }
    .tabs { display: flex; gap: 10px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
    .tab { padding: 10px 16px; cursor: pointer; font-size: 14px; color: var(--text-muted); border-bottom: 2px solid transparent; }
    .tab.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .content-box {
      background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 20px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 13px;
      line-height: 1.6; max-height: 600px; overflow-y: auto; white-space: pre-wrap;
    }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
    th, td { border: 1px solid var(--border); padding: 10px; text-align: left; }
    th { background: #1e293b; color: var(--accent); font-weight: 600; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: inline-block; }
    .badge-correct { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
    .badge-wrong { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .badge-unsupported { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-missing { background: rgba(148, 163, 184, 0.2); color: #cbd5e1; border: 1px solid #94a3b8; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>FIN 67110 Equity Research Desk</h1>
        <div class="subtitle">Autonomous Agent Team Graph (CrewAI Flows Architecture & Dual Verifier Node)</div>
      </div>
      <div>
        <span class="badge badge-correct">Rule: Process in Code · Node Work Dynamic</span>
      </div>
    </header>

    <div class="grid">
      <!-- Left Sidebar: Controls & Stepper -->
      <div>
        <div class="card">
          <div class="card-title">Run Agent Team Graph</div>
          <form id="runForm">
            <label for="ticker">Company Ticker Symbol</label>
            <input type="text" id="ticker" value="COST" required placeholder="e.g. COST">

            <label for="peers">Peer Tickers (Comma-separated)</label>
            <input type="text" id="peers" value="WMT,TGT,BJ" placeholder="e.g. WMT,TGT,BJ">

            <label for="price">Stock Price ($ USD for P/E)</label>
            <input type="number" step="0.01" id="price" value="920.00" placeholder="e.g. 920.00">

            <button type="submit" id="btnRun">Execute Agent Team Graph</button>
          </form>
        </div>

        <div class="card">
          <div class="card-title">Inspect Existing Run / Proof</div>
          <label for="runSelect">Select Saved Run Folder</label>
          <select id="runSelect"></select>
          <button class="secondary" id="btnLoad">Load Run Data</button>
          <button class="secondary" id="btnVerifyOnly" style="margin-top:6px;">Run Standalone Verifier</button>
        </div>

        <div class="card">
          <div class="card-title">Graph Execution Nodes</div>
          <div class="node-steps">
            <div class="node-step" id="node-steps"><span class="node-badge">1</span> Node 1: steps (Filings & Facts)</div>
            <div class="node-step" id="node-research_analyst"><span class="node-badge">2</span> Node 2: research_analyst</div>
            <div class="node-step" id="node-financial_analyst"><span class="node-badge">3</span> Node 3: financial_analyst</div>
            <div class="node-step" id="node-investment_advisor"><span class="node-badge">4</span> Node 4: investment_advisor</div>
            <div class="node-step" id="node-strategy_manager"><span class="node-badge">5</span> Node 5: strategy_manager</div>
            <div class="node-step" id="node-verifier"><span class="node-badge">6</span> Node 6: verifier (Mandatory)</div>
          </div>
        </div>
      </div>

      <!-- Right Main Panel: Tabs for Marks, Report, Node I/O -->
      <div>
        <div class="card">
          <div class="tabs">
            <div class="tab active" data-tab="tab-marks">Table of Marks</div>
            <div class="tab" data-tab="tab-report">Verified Report</div>
            <div class="tab" data-tab="tab-io">Node I/O (Audit Trail)</div>
            <div class="tab" data-tab="tab-logs">Console Logs</div>
          </div>

          <div id="tab-marks" class="tab-content active">
            <div id="marksContainer">
              <p style="color:var(--text-muted); font-size:14px;">No run selected. Execute the desk or choose a saved run on the left.</p>
            </div>
          </div>

          <div id="tab-report" class="tab-content">
            <div class="content-box" id="reportContent">Verified report markdown will appear here...</div>
          </div>

          <div id="tab-io" class="tab-content">
            <div class="content-box" id="ioContent">Node inputs and outputs JSON audit trail will appear here...</div>
          </div>

          <div id="tab-logs" class="tab-content">
            <div class="content-box" id="logContent">Live execution logs will stream here...</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
      });
    });

    // Populate run select
    async function loadRunList() {
      try {
        const res = await fetch('/api/runs');
        const runs = await res.json();
        const sel = document.getElementById('runSelect');
        sel.innerHTML = '';
        runs.forEach(r => {
          const opt = document.createElement('option');
          opt.value = r;
          opt.textContent = r;
          sel.appendChild(opt);
        });
        if (runs.length > 0) {
          loadSelectedRun(runs[0]);
        }
      } catch (e) {
        console.error(e);
      }
    }

    // Render markdown table as HTML
    function renderMarkdownTable(mdText) {
      if (!mdText) return '<p style="color:var(--text-muted);">No marks recorded.</p>';
      const lines = mdText.split('\\n');
      let html = '';
      let inTable = false;
      let headerPassed = false;

      for (let line of lines) {
        line = line.trim();
        if (line.startsWith('|') && line.endsWith('|')) {
          if (!inTable) {
            inTable = true;
            html += '<table>';
          }
          if (line.includes('---')) {
            headerPassed = true;
            continue;
          }
          const cells = line.split('|').slice(1, -1).map(c => c.trim());
          if (!headerPassed) {
            html += '<tr>' + cells.map(c => `<th>${c}</th>`).join('') + '</tr>';
          } else {
            html += '<tr>' + cells.map(c => {
              let content = c.replace(/`/g, '');
              if (c.includes('**Correct**')) {
                return `<td><span class="badge badge-correct">Correct</span></td>`;
              } else if (c.includes('**Wrong**')) {
                return `<td><span class="badge badge-wrong">Wrong</span></td>`;
              } else if (c.includes('**Unsupported**')) {
                return `<td><span class="badge badge-unsupported">Unsupported</span></td>`;
              } else if (c.includes('**Missing**')) {
                return `<td><span class="badge badge-missing">Missing</span></td>`;
              }
              return `<td>${content}</td>`;
            }).join('') + '</tr>';
          }
        } else {
          if (inTable) {
            html += '</table>';
            inTable = false;
            headerPassed = false;
          }
          if (line.startsWith('###')) {
            html += `<h3 style="margin-top:16px; margin-bottom:8px; color:var(--accent); font-size:16px;">${line.replace(/###/g, '')}</h3>`;
          } else if (line.length > 0) {
            html += `<p style="margin-bottom:8px; font-size:13px;">${line.replace(/\\*\\*/g, '<b>')}</p>`;
          }
        }
      }
      if (inTable) html += '</table>';
      return html;
    }

    // Load data from specific run
    async function loadSelectedRun(runName) {
      const res = await fetch(`/api/run-details?run_id=${encodeURIComponent(runName)}`);
      const data = await res.json();
      document.getElementById('marksContainer').innerHTML = renderMarkdownTable(data.marks);
      document.getElementById('reportContent').textContent = data.report || "No report text.";
      document.getElementById('ioContent').textContent = JSON.stringify(data.node_io, null, 2);
    }

    document.getElementById('btnLoad').addEventListener('click', () => {
      const run = document.getElementById('runSelect').value;
      if (run) loadSelectedRun(run);
    });

    // Run Standalone Verifier
    document.getElementById('btnVerifyOnly').addEventListener('click', async () => {
      const run = document.getElementById('runSelect').value;
      if (!run) return;
      alert(`Running Verifier Node on ${run}...`);
      const res = await fetch('/api/verify-only', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_folder: run })
      });
      const data = await res.json();
      loadSelectedRun(run);
      alert('Verifier completed! Marks updated.');
    });

    // Submit Run Form
    document.getElementById('runForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const ticker = document.getElementById('ticker').value;
      const peers = document.getElementById('peers').value;
      const price = parseFloat(document.getElementById('price').value);

      document.getElementById('btnRun').disabled = true;
      document.getElementById('btnRun').textContent = 'Graph Executing...';

      // Highlight nodes sequentially
      const nodeNames = ['steps', 'research_analyst', 'financial_analyst', 'investment_advisor', 'strategy_manager', 'verifier'];
      nodeNames.forEach(n => {
        const el = document.getElementById(`node-${n}`);
        if (el) { el.className = 'node-step'; }
      });

      try {
        const res = await fetch('/api/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker, peers, price })
        });
        const result = await res.json();
        pollStatus();
      } catch (err) {
        alert(err);
        document.getElementById('btnRun').disabled = false;
        document.getElementById('btnRun').textContent = 'Execute Agent Team Graph';
      }
    });

    // Poll Status
    let pollInterval = null;
    function pollStatus() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(async () => {
        const res = await fetch('/api/status');
        const st = await res.json();
        document.getElementById('logContent').textContent = st.logs.join('\\n');

        if (st.current_node) {
          const el = document.getElementById(`node-${st.current_node}`);
          if (el) el.className = 'node-step active';
        }

        if (st.status === 'completed' || st.status === 'error') {
          clearInterval(pollInterval);
          document.getElementById('btnRun').disabled = false;
          document.getElementById('btnRun').textContent = 'Execute Agent Team Graph';
          
          // Mark all nodes done
          document.querySelectorAll('.node-step').forEach(n => n.className = 'node-step done');
          await loadRunList();
          if (st.last_run_dir) {
            document.getElementById('runSelect').value = st.last_run_dir;
            loadSelectedRun(st.last_run_dir);
          }
        }
      }, 1500);
    }

    // Init
    loadRunList();
  </script>
</body>
</html>
"""


class DeskUIRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif path == "/api/runs":
            self._send_json(get_available_runs())
        elif path == "/api/status":
            global RUN_STATE
            self._send_json(RUN_STATE)
        elif path == "/api/run-details":
            query = urllib.parse.parse_qs(parsed.query)
            run_id = query.get("run_id", [""])[0]
            self._send_json(load_run_data(run_id))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            params = json.loads(body)
        except Exception:
            params = {}

        if path == "/api/run":
            ticker = params.get("ticker", "COST").strip().upper()
            peers_raw = params.get("peers", "")
            peers = [p.strip().upper() for p in peers_raw.split(",") if p.strip()]
            price = params.get("price")
            if price:
                try:
                    price = float(price)
                except ValueError:
                    price = None

            t = threading.Thread(target=run_agent_team_worker, args=(ticker, peers, price), daemon=True)
            t.start()
            self._send_json({"status": "started", "ticker": ticker})

        elif path == "/api/verify-only":
            folder = params.get("run_folder", "")
            base_dir = Path(__file__).resolve().parent
            run_dir = base_dir / folder
            if not run_dir.exists():
                run_dir = Path(r"C:\Users\cashi") / folder
            if run_dir.exists():
                verifier.run_verifier(run_dir)
                self._send_json({"status": "verified", "folder": folder})
            else:
                self._send_json({"status": "error", "message": "Folder not found"}, status=400)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default stdout logging
        pass


def start_server():
    server_address = (HOST, PORT)
    with socketserver.TCPServer(server_address, DeskUIRequestHandler) as httpd:
        url = f"http://{HOST}:{PORT}"
        print("=" * 80)
        print("FIN 67110 - Equity Research Desk UI")
        print(f"Server started at: {url}")
        print("Press Ctrl+C to terminate the UI server.")
        print("=" * 80)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down UI server.")


if __name__ == "__main__":
    start_server()
