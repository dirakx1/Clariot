"""
Greenhouse Dashboard App — client application for the Clariot agent.

Exposes a minimal FastAPI UI that talks to the agent's control plane
(Agentcontainer/control_plane/server.py) via HTTP and WebSocket.

Run:
    uvicorn examples.greenhouse_monitoring.app:app --port 3000

Expects AGENT_URL env var pointing at the agent's control plane.
Default: http://localhost:8080
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8080")

app = FastAPI(title="Greenhouse Dashboard")


# ---------------------------------------------------------------------------
# HTML dashboard (single-file, no build step required)
# ---------------------------------------------------------------------------

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Greenhouse Dashboard</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; }
  h1   { color: #58a6ff; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px;
          padding: 1rem; margin: 1rem 0; }
  .label { color: #8b949e; font-size: 0.85em; }
  .value { font-size: 1.4em; font-weight: bold; color: #79c0ff; }
  .ok    { color: #3fb950; }
  .warn  { color: #d29922; }
  .crit  { color: #f85149; }
  input  { background: #21262d; color: #c9d1d9; border: 1px solid #30363d;
           padding: 0.5rem; border-radius: 4px; width: 70%; }
  button { background: #238636; color: #fff; border: none; padding: 0.5rem 1rem;
           border-radius: 4px; cursor: pointer; margin-left: 0.5rem; }
  pre    { background: #161b22; padding: 1rem; border-radius: 4px;
           overflow-x: auto; max-height: 300px; font-size: 0.8em; }
</style>
</head>
<body>
<h1>Greenhouse Agent Dashboard</h1>

<div class="card" id="sensors-card">
  <div class="label">Sensors — loading...</div>
</div>

<div class="card" id="actuators-card">
  <div class="label">Actuators — loading...</div>
</div>

<div class="card">
  <div class="label">Ask the agent</div><br>
  <input id="query" type="text" placeholder="e.g. Should I water the plants?">
  <button onclick="sendQuery()">Ask</button>
  <pre id="response"></pre>
</div>

<script>
const ws = new WebSocket(`ws://${location.host}/ws/live`);

ws.onmessage = (evt) => {
  const data = JSON.parse(evt.data);
  if (data.sensors) renderSensors(data.sensors);
  if (data.actuators) renderActuators(data.actuators);
};

function renderSensors(sensors) {
  const el = document.getElementById('sensors-card');
  let html = '<div class="label">Sensors</div>';
  for (const [id, s] of Object.entries(sensors)) {
    const v = s.value !== undefined ? s.value : s.error ?? '—';
    html += `<div><span class="label">${id}</span>
             &nbsp;<span class="value">${v} ${s.unit ?? ''}</span></div>`;
  }
  el.innerHTML = html;
}

function renderActuators(actuators) {
  const el = document.getElementById('actuators-card');
  let html = '<div class="label">Actuators</div>';
  for (const [id, a] of Object.entries(actuators)) {
    const badge = a.state === 'running' || a.state === 'open'
      ? 'ok' : (a.state === 'error' ? 'crit' : 'warn');
    html += `<div><span class="label">${id}</span>
             &nbsp;<span class="${badge}">${a.state}</span></div>`;
  }
  el.innerHTML = html;
}

async function sendQuery() {
  const q = document.getElementById('query').value.trim();
  if (!q) return;
  document.getElementById('response').textContent = 'Thinking…';
  const res = await fetch('/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: q})
  });
  const data = await res.json();
  document.getElementById('response').textContent =
    data.response ?? JSON.stringify(data, null, 2);
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.get("/status")
async def status():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{AGENT_URL}/agent/status", timeout=5)
        return r.json()


@app.get("/sensors")
async def sensors():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{AGENT_URL}/agent/sensors", timeout=5)
        return r.json()


@app.post("/query")
async def query(body: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{AGENT_URL}/agent/query",
            json={"message": body.get("message", "")},
            timeout=30,
        )
        return r.json()


@app.post("/command")
async def command(body: Dict[str, Any]):
    """Direct actuator command bypassing LLM reasoning."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{AGENT_URL}/agent/command",
            json=body,
            timeout=10,
        )
        return r.json()


# ---------------------------------------------------------------------------
# WebSocket — proxies live sensor + actuator state to the browser
# ---------------------------------------------------------------------------

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await websocket.accept()
    try:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    sensors_r = await client.get(f"{AGENT_URL}/agent/sensors", timeout=3)
                    status_r = await client.get(f"{AGENT_URL}/agent/status", timeout=3)

                    sensors = sensors_r.json().get("sensors", {})
                    actuators = status_r.json().get("current_state", {}).get("actuators", {})

                    await websocket.send_json({
                        "sensors": sensors,
                        "actuators": actuators,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                except Exception:
                    pass  # agent may be temporarily unavailable
                await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
