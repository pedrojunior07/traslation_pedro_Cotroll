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
      main { padding: 24px; display: grid; gap: 16px; }
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
      <div><a href="/admin/logout">Logout</a></div>
    </header>
    <main>
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
          <div class="row">
            <select id="ai_enabled">
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
            <input id="ai_base" placeholder="Base URL">
            <input id="ai_model" placeholder="Model">
            <input id="ai_key" placeholder="API Key">
          </div>
          <div class="toolbar">
            <button onclick="saveAI()">Salvar</button>
            <button class="btn-secondary" onclick="loadAI()">Recarregar</button>
            <span id="ai_status" class="status"></span>
          </div>
          <div class="muted">A chave so sera salva se for informada.</div>
        </div>
      </section>
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
          tr.innerHTML = `
            <td>${lic.id}</td>
            <td>${lic.key}</td>
            <td>${lic.type}</td>
            <td>${lic.max_devices}</td>
            <td>${lic.quota_type || ""} ${lic.quota_limit}</td>
            <td>${lic.quota_period}</td>
            <td>${expires}</td>
            <td>${days}</td>
            <td>${lic.is_active ? "yes" : "no"}</td>
            <td class="actions">
              <button class="btn-secondary" onclick="toggleLicense(${lic.id}, ${lic.is_active})">Ativar/Desativar</button>
              <button class="btn-danger" onclick="rotateKey(${lic.id})">Rotate</button>
            </td>
          `;
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
        await api(`/admin/api/licenses/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_active: !isActive }) });
        await loadLicenses();
      }

      async function rotateKey(id) {
        await api(`/admin/api/licenses/${id}/rotate-key`, { method: "POST" });
        await loadLicenses();
      }

      async function loadDevices() {
        setStatus("dev_status", "Carregando...");
        const data = await api("/admin/api/devices");
        const body = document.querySelector("#dev_table tbody");
        body.innerHTML = "";
        for (const dev of data) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${dev.id}</td>
            <td>${dev.license_id}</td>
            <td>${dev.device_id}</td>
            <td>${dev.device_name || ""}</td>
            <td>${dev.is_blocked ? "yes" : "no"}</td>
            <td>${dev.usage_today}</td>
            <td>${dev.usage_month_count}</td>
            <td>${dev.total_usage}</td>
            <td class="actions">
              <button class="btn-secondary" onclick="toggleDevice(${dev.id}, ${dev.is_blocked})">Block/Unblock</button>
              <button class="btn-danger" onclick="resetDevice(${dev.id})">Reset</button>
            </td>
          `;
          body.appendChild(tr);
        }
        setStatus("dev_status", "OK");
      }

      async function toggleDevice(id, isBlocked) {
        await api(`/admin/api/devices/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_blocked: !isBlocked }) });
        await loadDevices();
      }

      async function resetDevice(id) {
        await api(`/admin/api/devices/${id}/reset-usage`, { method: "POST" });
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

      async function loadAI() {
        const data = await api("/admin/api/settings/ai");
        document.getElementById("ai_enabled").value = data.enabled ? "true" : "false";
        document.getElementById("ai_base").value = data.base_url || "";
        document.getElementById("ai_model").value = data.model || "";
        setStatus("ai_status", "OK");
      }

      async function saveAI() {
        const payload = {
          enabled: document.getElementById("ai_enabled").value === "true",
          base_url: document.getElementById("ai_base").value || null,
          model: document.getElementById("ai_model").value || null
        };
        const key = document.getElementById("ai_key").value;
        if (key) payload.api_key = key;
        await api("/admin/api/settings/ai", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        document.getElementById("ai_key").value = "";
        setStatus("ai_status", "Salvo");
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
        "base_url": cfg.base_url,
        "model": cfg.model,
        "api_key_present": bool(cfg.api_key),
    }


@router.put("/admin/api/settings/ai")
def admin_set_ai(request: Request, payload: dict, db: Session = Depends(get_db)):
    _get_admin(db, request)
    cfg = db.query(AIConfig).first()
    if not cfg:
        cfg = AIConfig()
    if "enabled" in payload:
        cfg.enabled = bool(payload.get("enabled"))
    if payload.get("base_url") is not None:
        cfg.base_url = payload.get("base_url")
    if payload.get("model") is not None:
        cfg.model = payload.get("model")
    if payload.get("api_key") is not None:
        cfg.api_key = payload.get("api_key")
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
