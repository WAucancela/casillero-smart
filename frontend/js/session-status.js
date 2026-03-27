<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Session Status Widget</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    /* ── Indicador de sesión en el navbar ── */
    .session-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      border: none;
      background: transparent;
      transition: background 0.2s;
    }
    .session-badge:hover { background: rgba(0,0,0,0.05); }
    .session-badge .dot {
      width: 7px; height: 7px; border-radius: 50%;
      flex-shrink: 0;
    }
    .session-badge.valid   .dot { background: #28a745; animation: pulse-green 2s infinite; }
    .session-badge.warning .dot { background: #ffc107; animation: pulse-amber 1s infinite; }
    .session-badge.expired .dot { background: #dc3545; }

    @keyframes pulse-green {
      0%,100%{ box-shadow: 0 0 0 0   rgba(40,167,69,0.4); }
      50%    { box-shadow: 0 0 0 5px rgba(40,167,69,0);   }
    }
    @keyframes pulse-amber {
      0%,100%{ box-shadow: 0 0 0 0   rgba(255,193,7,0.5); }
      50%    { box-shadow: 0 0 0 5px rgba(255,193,7,0);   }
    }

    /* ── Popover de detalle ── */
    .session-popover {
      position: fixed;
      top: 60px;
      right: 12px;
      width: 280px;
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.15);
      border: 1px solid #e9ecef;
      z-index: 9999;
      display: none;
      overflow: hidden;
      animation: popIn .2s ease;
    }
    @keyframes popIn {
      from { opacity:0; transform:translateY(-8px); }
      to   { opacity:1; transform:translateY(0);    }
    }
    .session-popover.open { display: block; }
    .pop-header {
      background: #f8f9fa;
      padding: 12px 16px;
      border-bottom: 1px solid #e9ecef;
      font-size: 12px;
      font-weight: 600;
      color: #495057;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .pop-body { padding: 14px 16px; }
    .pop-row  { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; font-size:13px; }
    .pop-row:last-child { margin-bottom:0; }
    .pop-label { color: #6c757d; }
    .pop-value { font-family: 'Courier New', monospace; font-size: 12px; color: #343a40; font-weight: 600; }
    .pop-value.green  { color: #28a745; }
    .pop-value.amber  { color: #856404; }
    .pop-value.red    { color: #dc3545; }
    .pop-countdown {
      background: linear-gradient(135deg, #e8f4fd, #f0fff4);
      border-radius: 8px;
      padding: 10px 14px;
      text-align: center;
      margin: 12px 0 0;
    }
    .pop-countdown .big { font-size: 22px; font-weight: 700; font-family: monospace; }
    .pop-countdown .sub { font-size: 11px; color: #6c757d; margin-top: 2px; }
    .pop-footer { padding: 10px 16px; border-top: 1px solid #f0f0f0; display:flex; gap:8px; }
    .pop-btn {
      flex: 1; padding: 7px 0; border-radius: 6px; border: none;
      font-size: 12px; font-weight: 600; cursor: pointer; transition: all .15s;
    }
    .pop-btn:hover { opacity: 0.85; transform: translateY(-1px); }
    .pop-btn.primary { background: #007bff; color: #fff; }
    .pop-btn.danger  { background: #fff0f0; color: #dc3545; border: 1px solid #f5c6cb; }
  </style>
</head>
<body>

<!--
  ════════════════════════════════════════════
  COMPONENTE: Indicador de sesión en el navbar

  Incluir en el navbar de cada página así:

    <li class="nav-item" id="session-nav-item"></li>

  Luego al final del HTML (después de cargar auth.js):

    <script src="js/session-status.js"></script>
    <script>SessionStatus.init("session-nav-item");</script>
  ════════════════════════════════════════════
-->

<script src="js/auth.js"></script>
<script>
// ══════════════════════════════════════════════════════════════
//  session-status.js
//  Indicador visual de la sesión JWT en el navbar.
//  Muestra tiempo restante, estado, y permite renovar/cerrar.
// ══════════════════════════════════════════════════════════════

window.SessionStatus = {
  _timer: null,
  _popoverOpen: false,

  init(navItemId) {
    const navItem = document.getElementById(navItemId);
    if (!navItem) return;

    // Insertar el badge
    navItem.innerHTML = `
      <button class="nav-link session-badge valid" id="ss-badge" onclick="SessionStatus.togglePopover()">
        <span class="dot"></span>
        <span id="ss-label">Sesión activa</span>
      </button>
      <div class="session-popover" id="ss-popover">
        <div class="pop-header"><i class="fas fa-shield-alt mr-2"></i>Información de sesión</div>
        <div class="pop-body" id="ss-popover-body"></div>
        <div class="pop-footer">
          <button class="pop-btn primary" onclick="SessionStatus.renovar()">
            <i class="fas fa-sync mr-1"></i>Renovar ahora
          </button>
          <button class="pop-btn danger" onclick="API.auth.logout()">
            <i class="fas fa-sign-out-alt mr-1"></i>Cerrar sesión
          </button>
        </div>
      </div>`;

    // Cerrar popover al hacer click fuera
    document.addEventListener("click", e => {
      const badge   = document.getElementById("ss-badge");
      const popover = document.getElementById("ss-popover");
      if (badge && popover && !badge.contains(e.target) && !popover.contains(e.target)) {
        this.closePopover();
      }
    });

    this._tick();
    this._timer = setInterval(() => this._tick(), 5000);
  },

  _tick() {
    const info = AuthModule.getTokenInfo();
    if (!info) return;

    const badge = document.getElementById("ss-badge");
    const label = document.getElementById("ss-label");
    if (!badge || !label) return;

    const secs    = info.expiresInSec;
    const mins    = Math.floor(secs / 60);
    const horas   = Math.floor(mins / 60);
    const minRest = mins % 60;

    let estado, labelTxt, colorClass;

    if (info.expired) {
      estado     = "expired";
      labelTxt   = "Sesión expirada";
      colorClass = "red";
    } else if (mins < 10) {
      estado     = "warning";
      labelTxt   = `Expira en ${mins}m`;
      colorClass = "amber";
    } else {
      estado     = "valid";
      labelTxt   = horas > 0 ? `${horas}h ${minRest}m` : `${mins}m`;
      colorClass = "green";
    }

    badge.className = `nav-link session-badge ${estado}`;
    label.textContent = labelTxt;

    if (this._popoverOpen) this._renderPopover(info, secs, colorClass);
  },

  _renderPopover(info, secs, colorClass) {
    const body = document.getElementById("ss-popover-body");
    if (!body) return;

    const hh = String(Math.floor(secs / 3600)).padStart(2,"0");
    const mm = String(Math.floor((secs % 3600)/60)).padStart(2,"0");
    const ss = String(secs % 60).padStart(2,"0");
    const countdownColor = colorClass === "red" ? "#dc3545" : colorClass === "amber" ? "#856404" : "#007bff";

    body.innerHTML = `
      <div class="pop-row">
        <span class="pop-label">Usuario</span>
        <span class="pop-value">${AuthModule.getEmail()}</span>
      </div>
      <div class="pop-row">
        <span class="pop-label">Expira a las</span>
        <span class="pop-value ${colorClass}">${info.expiresAt.split(" ")[1] || info.expiresAt}</span>
      </div>
      <div class="pop-row">
        <span class="pop-label">Estado</span>
        <span class="pop-value ${colorClass}">${info.expired ? "EXPIRADO" : "ACTIVO"}</span>
      </div>
      <div class="pop-countdown">
        <div class="big" style="color:${countdownColor}">${hh}:${mm}:${ss}</div>
        <div class="sub">tiempo restante de la sesión</div>
      </div>`;
  },

  togglePopover() {
    this._popoverOpen = !this._popoverOpen;
    const pop = document.getElementById("ss-popover");
    if (pop) pop.classList.toggle("open", this._popoverOpen);
    if (this._popoverOpen) {
      const info = AuthModule.getTokenInfo();
      if (info) this._renderPopover(info, info.expiresInSec, info.expired ? "red" : info.expiresInSec < 600 ? "amber" : "green");
    }
  },

  closePopover() {
    this._popoverOpen = false;
    const pop = document.getElementById("ss-popover");
    if (pop) pop.classList.remove("open");
  },

  async renovar() {
    const badge = document.getElementById("ss-badge");
    const label = document.getElementById("ss-label");
    if (label) label.textContent = "Renovando...";
    try {
      await AuthModule.getAccessToken();
      if (label) label.textContent = "Renovado ✓";
      setTimeout(() => this._tick(), 1500);
    } catch {
      if (label) label.textContent = "Error al renovar";
    }
    this.closePopover();
  },
};
</script>

</body>
</html>
