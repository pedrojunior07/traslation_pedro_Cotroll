from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from api.config import Settings
from api.database import get_db
from api.models import AIConfig, Device, License, User
from api.security import create_token, decode_token, verify_password

router = APIRouter()
settings_cfg = Settings()

def _generate_key() -> str:
    return f"LIC-{int(datetime.utcnow().timestamp())}-{datetime.utcnow().microsecond}"


def _apply_duration(expires_at: str | None, duration_days: int | None) -> datetime | None:
    if expires_at:
        try:
            return datetime.fromisoformat(expires_at)
        except ValueError:
            return None
    if duration_days and duration_days > 0:
        return datetime.utcnow() + timedelta(days=duration_days)
    return None


def _license_payload(license_obj: License) -> dict:
    return {
        "id": license_obj.id,
        "key": license_obj.key,
        "type": license_obj.type,
        "max_devices": license_obj.max_devices,
        "quota_type": license_obj.quota_type,
        "quota_limit": license_obj.quota_limit,
        "quota_period": license_obj.quota_period,
        "duration_days": license_obj.duration_days,
        "is_active": license_obj.is_active,
        "expires_at": license_obj.expires_at,
        "created_at": license_obj.created_at,
        "days_remaining": license_obj.days_remaining,
    }


def _get_admin(db: Session, request: Request) -> User:
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    subject, kind = decode_token(token)
    if kind != "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(subject)).first()
    if not user or not user.is_active or not user.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def get_admin(request: Request, db: Session = Depends(get_db)) -> User:
    return _get_admin(db, request)


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request) -> str:
    error = request.query_params.get("error")
    msg = "<p class='error'>Invalid credentials</p>" if error else ""
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Admin Login</title>
    <style>
      :root {{
        --bg: #0b1020;
        --card: #121a2f;
        --accent: #f97316;
        --accent-2: #22c55e;
        --text: #e5e7eb;
        --muted: #94a3b8;
        --line: rgba(148, 163, 184, 0.2);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        font-family: "Bahnschrift", "Candara", "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(1200px 600px at 10% 10%, rgba(249, 115, 22, 0.18), transparent 60%),
          radial-gradient(800px 400px at 90% 15%, rgba(34, 197, 94, 0.18), transparent 60%),
          var(--bg);
        padding: 32px;
      }}
      .card {{
        width: min(420px, 100%);
        background: linear-gradient(160deg, rgba(18, 26, 47, 0.95), rgba(18, 26, 47, 0.75));
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 30px 80px rgba(0,0,0,0.45);
      }}
      h2 {{
        margin: 0 0 8px;
        font-size: 22px;
        letter-spacing: 0.5px;
      }}
      .sub {{
        color: var(--muted);
        margin: 0 0 18px;
        font-size: 13px;
      }}
      .row {{ margin-bottom: 14px; }}
      label {{ display: block; margin-bottom: 6px; color: var(--muted); font-size: 12px; }}
      input {{
        width: 100%;
        padding: 12px 12px;
        border: 1px solid var(--line);
        border-radius: 10px;
        background: #0f162b;
        color: var(--text);
      }}
      button {{
        width: 100%;
        padding: 12px;
        background: linear-gradient(90deg, var(--accent), #fb923c);
        color: #0b1020;
        border: 0;
        border-radius: 10px;
        font-weight: 700;
        cursor: pointer;
      }}
      .error {{
        color: #fecaca;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 8px 10px;
        border-radius: 10px;
        margin: 0 0 12px;
        font-size: 13px;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <h2>Tradutor Master</h2>
      <p class="sub">Acesso administrativo</p>
      {msg}
      <form method="post" action="/admin/login">
        <div class="row">
          <label>Username</label>
          <input name="username" autocomplete="username" required>
        </div>
        <div class="row">
          <label>Password</label>
          <input type="password" name="password" autocomplete="current-password" required>
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  </body>
</html>
"""


@router.post("/admin/login")
def admin_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash) or not user.is_superadmin:
        return RedirectResponse(url="/admin/login?error=1", status_code=status.HTTP_303_SEE_OTHER)
    token = create_token(str(user.id), "user", 12 * 60)
    resp = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie("admin_token", token, httponly=True, samesite="lax")
    return resp


@router.get("/admin/logout")
def admin_logout() -> RedirectResponse:
    resp = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie("admin_token")
    return resp


@router.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(get_db)) -> str:
    _get_admin(db, request)
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Tradutor Master Admin</title>
    <style>
      :root {
        --bg: #0b1020;
        --panel: #0f172a;
        --card: #131c33;
        --accent: #f97316;
        --accent-2: #22c55e;
        --muted: #94a3b8;
        --text: #e5e7eb;
        --line: rgba(148, 163, 184, 0.2);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Bahnschrift", "Candara", "Segoe UI", sans-serif;
        background:
          radial-gradient(1200px 600px at 10% 10%, rgba(249, 115, 22, 0.15), transparent 60%),
          radial-gradient(900px 500px at 90% 20%, rgba(34, 197, 94, 0.12), transparent 60%),
          var(--bg);
        color: var(--text);
      }
      header {
        background: linear-gradient(90deg, #0b1020, #0f172a);
        border-bottom: 1px solid var(--line);
        color: #fff;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 10;
      }
      header .brand { font-weight: 700; letter-spacing: 0.6px; }
      header .tag { color: var(--muted); font-size: 12px; }
      .tabs { display: flex; gap: 8px; margin-bottom: 16px; padding: 0 24px; padding-top: 16px; }
      .tab { padding: 10px 20px; background: transparent; border: 1px solid var(--line); border-radius: 8px 8px 0 0; cursor: pointer; color: var(--muted); transition: all 0.3s; }
      .tab.active { background: var(--card); color: var(--text); border-bottom: 1px solid var(--card); }
      .tab-content { display: none; }
      .tab-content.active { display: block; }
      main { padding: 0 24px 24px; display: grid; gap: 16px; }
      section {
        background: linear-gradient(160deg, rgba(19, 28, 51, 0.95), rgba(19, 28, 51, 0.75));
        border: 1px solid var(--line);
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 18px 50px rgba(0,0,0,0.35);
      }
      h2 { margin: 0 0 12px; font-size: 16px; }
      table { width: 100%; border-collapse: collapse; font-size: 13px; }
      th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--line); }
      th { color: var(--muted); font-weight: 600; }
      .row { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 8px; margin-bottom: 10px; }
      input, select {
        padding: 8px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #0f162b;
        color: var(--text);
      }
      button {
        padding: 8px 12px;
        border: 0;
        border-radius: 8px;
        background: linear-gradient(90deg, var(--accent), #fb923c);
        color: #0b1020;
        cursor: pointer;
        font-weight: 600;
      }
      .btn-secondary { background: #1f2937; color: #e5e7eb; }
      .btn-danger { background: #ef4444; color: #0b1020; }
      .actions { display: flex; gap: 6px; flex-wrap: wrap; }
      .muted { color: var(--muted); font-size: 12px; }
      .toolbar { display: flex; gap: 8px; margin-bottom: 10px; align-items: center; }
      .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      .status { margin-left: 12px; color: var(--accent-2); font-weight: 600; font-size: 12px; }
      .hint { color: var(--muted); font-size: 12px; margin-top: 6px; }
      .hint { color: var(--muted); font-size: 12px; margin-top: 6px; }
      a { color: #e5e7eb; text-decoration: none; }
    </style>
  </head>
  <body>
    <header>
      <div>
        <div class="brand">Tradutor Master Admin</div>
        <div class="tag">Painel de licencas e dispositivos</div>
      </div>
      <div style="display: flex; gap: 16px; align-items: center;">
        <a href="/admin/logout">Logout</a>
      </div>
    </header>
    <div class="tabs">
      <div class="tab active" data-tab="licencas" onclick="switchTab('licencas', this)">Licenças</div>
      <div class="tab" data-tab="testes" onclick="switchTab('testes', this)">Testes IA</div>
    </div>
    <main>
    <div id="tab-licencas" class="tab-content active">
      <section>
        <h2>Licencas</h2>
        <div class="row">
          <input id="lic_type" placeholder="Tipo">
          <input id="lic_devices" placeholder="Max devices" value="1" disabled>
          <select id="lic_quota_type">
            <option>TRANSLATIONS</option>
            <option>PAGES</option>
          </select>
          <input id="lic_quota_limit" placeholder="Quota limit" value="500">
          <select id="lic_quota_period">
            <option>DAILY</option>
            <option>MONTHLY</option>
            <option>TOTAL</option>
            <option>NONE</option>
          </select>
          <input id="lic_duration" placeholder="Duration days">
        </div>
        <div class="toolbar">
          <button onclick="createLicense()">Criar licenca</button>
          <button class="btn-secondary" onclick="loadLicenses()">Recarregar</button>
          <span id="lic_status" class="status"></span>
        </div>
        <table id="lic_table">
          <thead>
            <tr>
              <th>ID</th><th>Key</th><th>Type</th><th>Devices</th><th>Quota</th><th>Period</th><th>Expires</th><th>Days</th><th>Active</th><th>Actions</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </section>

      <section>
        <h2>Dispositivos</h2>
        <div class="toolbar">
          <button class="btn-secondary" onclick="loadDevices()">Recarregar</button>
          <span id="dev_status" class="status"></span>
        </div>
        <table id="dev_table">
          <thead>
            <tr>
              <th>ID</th><th>License</th><th>Device</th><th>Name</th><th>Blocked</th><th>Usage Today</th><th>Usage Month</th><th>Total</th><th>Actions</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </section>

      <section class="grid-2">
        <div>
          <h2>Config Translate</h2>
          <div class="row">
            <input id="tr_base" placeholder="Base URL" value="http://102.211.186.44/translate" disabled>
            <input id="tr_timeout" placeholder="Timeout" disabled>
          </div>
          <div class="toolbar">
            <button onclick="saveTranslate()" disabled>Salvar</button>
            <button class="btn-secondary" onclick="loadTranslate()">Recarregar</button>
            <span id="tr_status" class="status"></span>
          </div>
          <div class="hint">Configuracao fixa no backend.</div>
        </div>
        <div>
          <h2>Config IA</h2>
          <div class="row" style="grid-template-columns: auto 1fr 1fr;">
            <select id="ai_enabled" onchange="toggleAIEnabled()">
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
            <select id="ai_provider" onchange="toggleProviderFields()">
              <option value="openai">OpenAI</option>
              <option value="gemini">Gemini</option>
              <option value="grok">Grok</option>
            </select>
            <input id="ai_timeout" placeholder="Timeout (s)" type="number" value="30">
          </div>
          <div id="openai_fields" style="display: none;">
            <div class="row" style="grid-template-columns: 1fr 1fr 1fr;">
              <input id="ai_base" placeholder="OpenAI Base URL">
              <input id="ai_model" placeholder="OpenAI Model">
              <input id="ai_key" placeholder="OpenAI API Key" type="password">
            </div>
          </div>
          <div id="gemini_fields" style="display: none;">
            <div class="row" style="grid-template-columns: 1fr 1fr;">
              <div style="display: flex; gap: 8px;">
                <select id="gemini_model" style="flex: 1;">
                  <option value="">Selecione um modelo...</option>
                </select>
                <button type="button" onclick="loadGeminiModels()" class="btn-secondary" style="padding: 0 12px; white-space: nowrap;">🔄 Carregar</button>
              </div>
              <input id="gemini_key" placeholder="Gemini API Key" type="password">
            </div>
          </div>
          <div id="grok_fields" style="display: none;">
            <div class="row" style="grid-template-columns: 1fr 1fr;">
              <input id="grok_model" placeholder="Grok Model">
              <input id="grok_key" placeholder="Grok API Key" type="password">
            </div>
          </div>
          <div class="toolbar">
            <button onclick="saveAI()">Salvar</button>
            <button class="btn-secondary" onclick="loadAI()">Recarregar</button>
            <span id="ai_status" class="status"></span>
          </div>
          <div class="muted">Salve a configuração, depois teste na aba "🧪 Testes IA".</div>
        </div>
      </section>
    </div>

    <div id="tab-testes" class="tab-content">
      <section>
        <h2>🔄 Tradução em Lote (IA)</h2>
        <p class="muted">Envia múltiplos tokens e recebe todas traduções de uma vez.</p>
        <div style="margin-top: 12px;">
          <label style="display: block; margin-bottom: 6px; color: var(--muted); font-size: 12px;">Tokens JSON:</label>
          <textarea id="batch_tokens" style="width: 100%; min-height: 200px; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #0f162b; color: var(--text); font-family: monospace; font-size: 12px;">{
  "tokens": [
    {"location": "Parágrafo 1", "text": "Hello World"},
    {"location": "Parágrafo 2", "text": "How are you?"},
    {"location": "Parágrafo 3", "text": "This is a test"}
  ],
  "source": "en",
  "target": "pt"
}</textarea>
        </div>
        <div class="row" style="grid-template-columns: 1fr 1fr; margin-top: 12px;">
          <input id="batch_source" placeholder="Idioma origem (ex: en)" value="en">
          <input id="batch_target" placeholder="Idioma destino (ex: pt)" value="pt">
        </div>
        <div class="toolbar" style="margin-top: 12px;">
          <button onclick="testBatchTranslate()">▶️ Traduzir Lote</button>
          <button class="btn-secondary" onclick="clearBatchResult()">Limpar</button>
          <span id="batch_status" class="status"></span>
        </div>
        <div id="batch_result" style="margin-top: 12px; padding: 12px; background: #0f162b; border: 1px solid var(--line); border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; display: none;"></div>
      </section>

      <section>
        <h2>📝 Tradução Individual (IA)</h2>
        <div class="row" style="grid-template-columns: 1fr 1fr;">
          <input id="single_source" placeholder="Idioma origem" value="en">
          <input id="single_target" placeholder="Idioma destino" value="pt">
        </div>
        <textarea id="single_text" placeholder="Texto para traduzir..." style="width: 100%; min-height: 100px; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #0f162b; color: var(--text); margin-top: 10px;">Hello, how are you today?</textarea>
        <div class="toolbar" style="margin-top: 12px;">
          <button onclick="testSingleTranslate()">▶️ Traduzir</button>
          <button class="btn-secondary" onclick="clearSingleResult()">Limpar</button>
          <span id="single_status" class="status"></span>
        </div>
        <div id="single_result" style="margin-top: 12px; padding: 12px; background: #0f162b; border: 1px solid var(--line); border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; display: none;"></div>
      </section>

      <section>
        <h2>📊 Informações do Sistema</h2>
        <div class="grid-2">
          <div>
            <h3 style="font-size: 14px; margin-bottom: 8px;">Provedor Atual</h3>
            <div id="info_provider" style="padding: 10px; background: #0f162b; border: 1px solid var(--line); border-radius: 8px; font-size: 13px;">-</div>
          </div>
          <div>
            <h3 style="font-size: 14px; margin-bottom: 8px;">Modelo Configurado</h3>
            <div id="info_model" style="padding: 10px; background: #0f162b; border: 1px solid var(--line); border-radius: 8px; font-size: 13px;">-</div>
          </div>
        </div>
        <div class="toolbar" style="margin-top: 12px;">
          <button class="btn-secondary" onclick="loadSystemInfo()">🔄 Atualizar Info</button>
        </div>
      </section>
    </div>
    </main>
    <script>
      async function api(path, options) {
        const resp = await fetch(path, options || {});
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(text || resp.status);
        }
        const contentType = resp.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          return resp.json();
        }
        return null;
      }

      function setStatus(id, msg) {
        const el = document.getElementById(id);
        if (el) el.textContent = msg;
      }

      async function loadLicenses() {
        setStatus("lic_status", "Carregando...");
        const data = await api("/admin/api/licenses");
        const body = document.querySelector("#lic_table tbody");
        body.innerHTML = "";
        for (const lic of data) {
          const tr = document.createElement("tr");
          const expires = lic.expires_at ? lic.expires_at.split("T")[0] : "";
          const days = lic.days_remaining != null ? lic.days_remaining : "";
          tr.innerHTML =
            "<td>" + lic.id + "</td>" +
            "<td>" + lic.key + "</td>" +
            "<td>" + lic.type + "</td>" +
            "<td>" + lic.max_devices + "</td>" +
            "<td>" + (lic.quota_type || "") + " " + lic.quota_limit + "</td>" +
            "<td>" + lic.quota_period + "</td>" +
            "<td>" + expires + "</td>" +
            "<td>" + days + "</td>" +
            "<td>" + (lic.is_active ? "yes" : "no") + "</td>" +
            '<td class="actions">' +
              '<button class="btn-secondary" onclick="toggleLicense(' + lic.id + ', ' + lic.is_active + ')">Ativar/Desativar</button>' +
              '<button class="btn-danger" onclick="rotateKey(' + lic.id + ')">Rotate</button>' +
            "</td>";
          body.appendChild(tr);
        }
        setStatus("lic_status", "OK");
      }

      async function createLicense() {
        const payload = {
          type: document.getElementById("lic_type").value || "STANDARD",
          max_devices: 1,
          quota_type: document.getElementById("lic_quota_type").value || "TRANSLATIONS",
          quota_limit: parseInt(document.getElementById("lic_quota_limit").value || "0", 10),
          quota_period: document.getElementById("lic_quota_period").value || "DAILY",
          duration_days: parseInt(document.getElementById("lic_duration").value || "0", 10) || null,
          is_active: true
        };
        setStatus("lic_status", "Criando...");
        await api("/admin/api/licenses", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        await loadLicenses();
      }

      async function toggleLicense(id, isActive) {
        await api("/admin/api/licenses/" + id, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: !isActive }) });
        await loadLicenses();
      }

      async function rotateKey(id) {
        await api("/admin/api/licenses/" + id + "/rotate-key", { method: "POST" });
        await loadLicenses();
      }

      async function loadDevices() {
        setStatus("dev_status", "Carregando...");
        const data = await api("/admin/api/devices");
        const body = document.querySelector("#dev_table tbody");
        body.innerHTML = "";
        for (const dev of data) {
          const tr = document.createElement("tr");
          tr.innerHTML =
            "<td>" + dev.id + "</td>" +
            "<td>" + dev.license_id + "</td>" +
            "<td>" + dev.device_id + "</td>" +
            "<td>" + (dev.device_name || "") + "</td>" +
            "<td>" + (dev.is_blocked ? "yes" : "no") + "</td>" +
            "<td>" + dev.usage_today + "</td>" +
            "<td>" + dev.usage_month_count + "</td>" +
            "<td>" + dev.total_usage + "</td>" +
            '<td class="actions">' +
              '<button class="btn-secondary" onclick="toggleDevice(' + dev.id + ', ' + dev.is_blocked + ')">Block/Unblock</button>' +
              '<button class="btn-danger" onclick="resetDevice(' + dev.id + ')">Reset</button>' +
            "</td>";
          body.appendChild(tr);
        }
        setStatus("dev_status", "OK");
      }

      async function toggleDevice(id, isBlocked) {
        await api("/admin/api/devices/" + id, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_blocked: !isBlocked }) });
        await loadDevices();
      }

      async function resetDevice(id) {
        await api("/admin/api/devices/" + id + "/reset-usage", { method: "POST" });
        await loadDevices();
      }

      async function loadTranslate() {
        const data = await api("/admin/api/settings/translate");
        document.getElementById("tr_base").value = data.base_url || "";
        document.getElementById("tr_timeout").value = data.timeout || "";
        setStatus("tr_status", "OK");
      }

      async function saveTranslate() {
        await api("/admin/api/settings/translate", { method: "PUT", headers: { "Content-Type": "application/json" }, body: "{}" });
        setStatus("tr_status", "Fixo");
      }

      function toggleProviderFields() {
        const provider = document.getElementById("ai_provider").value;
        document.getElementById("openai_fields").style.display = provider === "openai" ? "block" : "none";
        document.getElementById("gemini_fields").style.display = provider === "gemini" ? "block" : "none";
        document.getElementById("grok_fields").style.display = provider === "grok" ? "block" : "none";
      }

      function toggleAIEnabled() {
        const enabled = document.getElementById("ai_enabled").value === "true";
        document.getElementById("ai_provider").disabled = !enabled;
        document.getElementById("ai_timeout").disabled = !enabled;

        // Disable/enable all provider-specific input fields
        const inputs = document.querySelectorAll('#openai_fields input, #gemini_fields input, #grok_fields input');
        inputs.forEach(input => input.disabled = !enabled);
      }

      document.getElementById("ai_provider").addEventListener("change", toggleProviderFields);

      async function loadGeminiModels() {
        try {
          setStatus("ai_status", "Carregando modelos...");
          const data = await api("/admin/api/gemini/models");

          const select = document.getElementById("gemini_model");
          const currentValue = select.value;

          // Limpar opções existentes
          select.innerHTML = '<option value="">Selecione um modelo...</option>';

          // Adicionar modelos disponíveis
          for (const model of data.models) {
            const option = document.createElement("option");
            option.value = model.name;
            option.textContent = model.displayName || model.name;
            option.title = model.description;
            select.appendChild(option);
          }

          // Restaurar valor selecionado se ainda existir
          if (currentValue) {
            select.value = currentValue;
          }

          setStatus("ai_status", data.models.length + " modelos carregados");
        } catch (error) {
          setStatus("ai_status", "✗ Erro ao carregar modelos");
          alert("Erro ao carregar modelos: " + error.message + "\\n\\nCertifique-se de que a API key do Gemini está configurada.");
        }
      }

      async function loadAI() {
        const data = await api("/admin/api/settings/ai");
        document.getElementById("ai_enabled").value = data.enabled ? "true" : "false";
        document.getElementById("ai_provider").value = data.provider || "openai";
        document.getElementById("ai_timeout").value = data.timeout || 30;

        // OpenAI fields
        document.getElementById("ai_base").value = data.base_url || "";
        document.getElementById("ai_model").value = data.model || "";
        if (data.api_key_present) {
          document.getElementById("ai_key").placeholder = "API Key (últimos 3: ...)";
        }

        // Gemini fields - add current model as option if set
        const geminiSelect = document.getElementById("gemini_model");
        if (data.gemini_model) {
          geminiSelect.innerHTML = '<option value="">Selecione um modelo...</option><option value="' + data.gemini_model + '" selected>' + data.gemini_model + '</option>';
        }
        if (data.gemini_api_key_present) {
          document.getElementById("gemini_key").placeholder = "API Key (últimos 3: ...)";
        }

        // Grok fields
        document.getElementById("grok_model").value = data.grok_model || "";
        if (data.grok_api_key_present) {
          document.getElementById("grok_key").placeholder = "API Key (últimos 3: ...)";
        }

        toggleProviderFields();
        toggleAIEnabled();
        setStatus("ai_status", "OK");
      }

      async function saveAI() {
        const provider = document.getElementById("ai_provider").value;
        const payload = {
          enabled: document.getElementById("ai_enabled").value === "true",
          provider: provider,
          timeout: parseFloat(document.getElementById("ai_timeout").value) || 30,
          max_retries: 3
        };

        // OpenAI fields
        if (provider === "openai") {
          payload.base_url = document.getElementById("ai_base").value || null;
          payload.model = document.getElementById("ai_model").value || null;
          const key = document.getElementById("ai_key").value;
          if (key) payload.api_key = key;
        }

        // Gemini fields
        if (provider === "gemini") {
          payload.gemini_model = document.getElementById("gemini_model").value || null;
          const key = document.getElementById("gemini_key").value;
          if (key) payload.gemini_api_key = key;
        }

        // Grok fields
        if (provider === "grok") {
          payload.grok_model = document.getElementById("grok_model").value || null;
          const key = document.getElementById("grok_key").value;
          if (key) payload.grok_api_key = key;
        }

        await api("/admin/api/settings/ai", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });

        // Limpar campos de senha
        document.getElementById("ai_key").value = "";
        document.getElementById("gemini_key").value = "";
        document.getElementById("grok_key").value = "";

        setStatus("ai_status", "Salvo");
      }

      function switchTab(tabName, element) {
        // Esconde todas as abas
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

        // Mostra aba selecionada
        document.getElementById('tab-' + tabName).classList.add('active');

        // Marca a tab clicada como ativa
        if (element) {
          element.classList.add('active');
        }

        // Carrega informações se for aba de testes
        if (tabName === 'testes') {
          loadSystemInfo();
        }
      }

      async function testBatchTranslate() {
        setStatus("batch_status", "Traduzindo...");
        try {
          const tokensData = JSON.parse(document.getElementById("batch_tokens").value);
          const source = document.getElementById("batch_source").value;
          const target = document.getElementById("batch_target").value;

          const result = await api("/admin/api/test/translate-batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              tokens: tokensData.tokens,
              source: source,
              target: target
            })
          });

          document.getElementById("batch_result").style.display = "block";
          document.getElementById("batch_result").textContent = JSON.stringify(result, null, 2);
          setStatus("batch_status", "✓ Sucesso");
        } catch (error) {
          document.getElementById("batch_result").style.display = "block";
          document.getElementById("batch_result").textContent = "Erro: " + error.message;
          setStatus("batch_status", "✗ Erro");
        }
      }

      async function testSingleTranslate() {
        setStatus("single_status", "Traduzindo...");
        try {
          const text = document.getElementById("single_text").value;
          const source = document.getElementById("single_source").value;
          const target = document.getElementById("single_target").value;

          const result = await api("/admin/api/test/translate-single", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              text: text,
              source: source,
              target: target
            })
          });

          document.getElementById("single_result").style.display = "block";
          document.getElementById("single_result").textContent = JSON.stringify(result, null, 2);
          setStatus("single_status", "✓ Sucesso");
        } catch (error) {
          document.getElementById("single_result").style.display = "block";
          document.getElementById("single_result").textContent = "Erro: " + error.message;
          setStatus("single_status", "✗ Erro");
        }
      }

      function clearBatchResult() {
        document.getElementById("batch_result").style.display = "none";
        document.getElementById("batch_result").textContent = "";
        setStatus("batch_status", "");
      }

      function clearSingleResult() {
        document.getElementById("single_result").style.display = "none";
        document.getElementById("single_result").textContent = "";
        setStatus("single_status", "");
      }

      async function loadSystemInfo() {
        try {
          const data = await api("/admin/api/settings/ai");

          let providerText = data.provider.toUpperCase();
          if (data.enabled) {
            providerText += " (Ativado)";
          } else {
            providerText += " (Desativado)";
          }
          document.getElementById("info_provider").textContent = providerText;

          let modelText = "";
          if (data.provider === "openai") {
            modelText = (data.model || "N/A") + " (" + (data.base_url || "N/A") + ")";
          } else if (data.provider === "gemini") {
            modelText = data.gemini_model || "N/A";
          } else if (data.provider === "grok") {
            modelText = data.grok_model || "N/A";
          }
          document.getElementById("info_model").textContent = modelText;
        } catch (error) {
          document.getElementById("info_provider").textContent = "Erro ao carregar";
          document.getElementById("info_model").textContent = "Erro ao carregar";
        }
      }

      loadLicenses();
      loadDevices();
      loadTranslate();
      loadAI();
    </script>
  </body>
</html>
"""


@router.get("/admin/api/licenses")
def admin_list_licenses(request: Request, db: Session = Depends(get_db)):
    _get_admin(db, request)
    licenses = db.query(License).order_by(License.id.asc()).all()
    return [_license_payload(lic) for lic in licenses]


@router.post("/admin/api/licenses")
def admin_create_license(request: Request, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    license_obj = License(
        key=_generate_key(),
        type=payload.get("type") or "STANDARD",
        max_devices=1,
        quota_type=payload.get("quota_type") or "TRANSLATIONS",
        quota_limit=int(payload.get("quota_limit") or 0),
        quota_period=payload.get("quota_period") or "DAILY",
        duration_days=payload.get("duration_days"),
        expires_at=_apply_duration(payload.get("expires_at"), payload.get("duration_days")),
        is_active=bool(payload.get("is_active", True)),
    )
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return _license_payload(license_obj)


@router.patch("/admin/api/licenses/{license_id}")
def admin_update_license(request: Request, license_id: int, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    if "type" in payload:
        license_obj.type = payload.get("type") or license_obj.type
    if "max_devices" in payload:
        license_obj.max_devices = 1
    if "quota_type" in payload:
        license_obj.quota_type = payload.get("quota_type") or license_obj.quota_type
    if "quota_limit" in payload:
        license_obj.quota_limit = int(payload.get("quota_limit") or license_obj.quota_limit)
    if "quota_period" in payload:
        license_obj.quota_period = payload.get("quota_period") or license_obj.quota_period
    if "duration_days" in payload or "expires_at" in payload:
        license_obj.duration_days = payload.get("duration_days") or license_obj.duration_days
        license_obj.expires_at = _apply_duration(payload.get("expires_at"), payload.get("duration_days"))
    if "is_active" in payload:
        license_obj.is_active = bool(payload.get("is_active"))
    license_obj.max_devices = 1
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return _license_payload(license_obj)


@router.post("/admin/api/licenses/{license_id}/rotate-key")
def admin_rotate_key(request: Request, license_id: int, db: Session = Depends(get_db)):
    _get_admin(db, request)
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")
    license_obj.key = _generate_key()
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)
    return _license_payload(license_obj)


@router.get("/admin/api/devices")
def admin_list_devices(request: Request, db: Session = Depends(get_db)):
    _get_admin(db, request)
    return db.query(Device).order_by(Device.id.asc()).all()


@router.patch("/admin/api/devices/{device_id}")
def admin_update_device(request: Request, device_id: int, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    for key, value in payload.items():
        setattr(device, key, value)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.post("/admin/api/devices/{device_id}/reset-usage")
def admin_reset_device(request: Request, device_id: int, db: Session = Depends(get_db)):
    _get_admin(db, request)
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    today = datetime.utcnow().date()
    device.usage_today = 0
    device.usage_today_date = today
    device.usage_month_count = 0
    device.usage_month_month = today.month
    device.usage_month_year = today.year
    db.add(device)
    db.commit()
    return {"status": "ok"}


@router.get("/admin/api/settings/ai")
def admin_get_ai(request: Request, db: Session = Depends(get_db)):
    _get_admin(db, request)
    cfg = db.query(AIConfig).first()
    if not cfg:
        cfg = AIConfig()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return {
        "enabled": cfg.enabled,
        "provider": cfg.provider,
        "base_url": cfg.base_url,
        "model": cfg.model,
        "api_key_present": bool(cfg.api_key),
        "gemini_api_key_present": bool(cfg.gemini_api_key),
        "gemini_model": cfg.gemini_model,
        "grok_api_key_present": bool(cfg.grok_api_key),
        "grok_model": cfg.grok_model,
        "timeout": cfg.timeout,
        "max_retries": cfg.max_retries,
    }


@router.put("/admin/api/settings/ai")
def admin_set_ai(request: Request, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    cfg = db.query(AIConfig).first()
    if not cfg:
        cfg = AIConfig()
    if "enabled" in payload:
        cfg.enabled = bool(payload.get("enabled"))
    if "provider" in payload:
        cfg.provider = payload.get("provider")
    if payload.get("base_url") is not None:
        cfg.base_url = payload.get("base_url")
    if payload.get("model") is not None:
        cfg.model = payload.get("model")
    if payload.get("api_key") is not None:
        cfg.api_key = payload.get("api_key")
    if payload.get("gemini_api_key") is not None:
        cfg.gemini_api_key = payload.get("gemini_api_key")
    if payload.get("gemini_model") is not None:
        cfg.gemini_model = payload.get("gemini_model")
    if payload.get("grok_api_key") is not None:
        cfg.grok_api_key = payload.get("grok_api_key")
    if payload.get("grok_model") is not None:
        cfg.grok_model = payload.get("grok_model")
    if "timeout" in payload:
        cfg.timeout = float(payload.get("timeout"))
    if "max_retries" in payload:
        cfg.max_retries = int(payload.get("max_retries"))
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return {"status": "ok"}


@router.get("/admin/api/settings/translate")
def admin_get_translate(request: Request, db: Session = Depends(get_db)):
    _get_admin(db, request)
    return {"base_url": settings_cfg.translate_base_url, "timeout": settings_cfg.translate_timeout}


@router.put("/admin/api/settings/translate")
def admin_set_translate(request: Request, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    return {"status": "readonly"}


@router.get("/admin/ai-test", response_class=HTMLResponse)
def admin_ai_test_page(request: Request, db: Session = Depends(get_db)) -> str:
    """Página de testes de IA integrada com autenticação admin."""
    from pathlib import Path

    _get_admin(db, request)

    html_file = Path(__file__).parent.parent / "templates" / "api_tester.html"
    return html_file.read_text(encoding="utf-8")


@router.post("/admin/api/test/translate-batch")
def admin_test_batch_translate(request: Request, payload: dict, db: Session = Depends(get_db)):
    """Testa tradução em lote sem precisar de device token."""
    _get_admin(db, request)

    from api.services import get_ai_provider

    tokens = payload.get("tokens", [])
    source = payload.get("source")
    target = payload.get("target")
    glossary = payload.get("glossary")

    if not tokens or not source or not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    try:
        provider = get_ai_provider(db)
        translations = provider.translate_batch(tokens, source, target, glossary)
        return {"translations": translations, "status": "success"}
    except Exception as e:
        import traceback
        error_detail = f"Translation error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)


@router.post("/admin/api/test/translate-single")
def admin_test_single_translate(request: Request, payload: dict, db: Session = Depends(get_db)):
    """Testa tradução individual sem precisar de device token."""
    _get_admin(db, request)

    from api.services import request_ai_translate

    text = payload.get("text")
    source = payload.get("source")
    target = payload.get("target")
    glossary = payload.get("glossary")

    if not text or not source or not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

    try:
        translated = request_ai_translate(db, text, source, target, glossary)
        return {"translatedText": translated, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Translation error: {str(e)}")


@router.get("/admin/api/gemini/models")
def admin_list_gemini_models(request: Request, db: Session = Depends(get_db)):
    """Lista modelos disponíveis do Gemini."""
    _get_admin(db, request)

    import requests

    cfg = db.query(AIConfig).first()
    if not cfg or not cfg.gemini_api_key:
        raise HTTPException(status_code=400, detail="Gemini API key não configurada")

    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": cfg.gemini_api_key}

        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Gemini API error: {resp.status_code} {resp.text}")

        data = resp.json()
        models = data.get("models", [])

        # Filtrar apenas modelos que suportam generateContent
        available_models = []
        for model in models:
            model_name = model.get("name", "")
            supported_methods = model.get("supportedGenerationMethods", [])

            if "generateContent" in supported_methods:
                # Extrair apenas o nome do modelo (remover "models/" prefix)
                clean_name = model_name.replace("models/", "")
                available_models.append({
                    "name": clean_name,
                    "displayName": model.get("displayName", clean_name),
                    "description": model.get("description", "")
                })

        return {"models": available_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")
