// ══════════════════════════════════════════════════════════════
//  api-client.js — Cliente HTTP
//  Depende de auth.js (debe cargarse antes)
// ══════════════════════════════════════════════════════════════

const API_BASE = window.API_BASE_URL || "/api";
// ──────────────────────────────────────────────────────────────
//  Clase de error con código HTTP
// ──────────────────────────────────────────────────────────────
class APIError extends Error {
  constructor(status, message) {
    super(message);
    this.status  = status;
    this.name    = "APIError";
  }
}

// ──────────────────────────────────────────────────────────────
//  Fetch base — obtiene siempre un token fresco
// ──────────────────────────────────────────────────────────────
async function request(method, endpoint, body = null, auth = true) {
  const headers = { "Content-Type": "application/json" };

  if (auth) {
    // getAccessToken() renueva automáticamente si está a punto de expirar
    const token = await AuthModule.getAccessToken();
    if (!token) {
      // Sin token válido → el logout ya fue disparado por auth.js
      return;
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const opts = { method, headers };
  if (body !== null) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(API_BASE + endpoint, opts);
  } catch {
    throw new APIError(0, "Sin conexión con el servidor.");
  }

  // 401 después de un token que parecía válido → forzar refresh una vez
  if (res.status === 401 && auth) {
    const nuevoToken = await AuthModule.getAccessToken();
    if (nuevoToken) {
      headers["Authorization"] = `Bearer ${nuevoToken}`;
      try {
        res = await fetch(API_BASE + endpoint, { method, headers, body: opts.body });
      } catch {
        throw new APIError(0, "Sin conexión con el servidor.");
      }
    }
    // Si sigue siendo 401 tras el retry → auth.js cerrará la sesión
    if (res.status === 401) {
      AuthModule.logout("session_expired");
      return;
    }
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const j = await res.json();
      const raw = j.detail || j.mensaje || j.message || detail;
      // Pydantic devuelve detail como array de objetos en errores 422
      detail = Array.isArray(raw)
        ? raw.map(e => e.msg || e.message || JSON.stringify(e)).join(", ")
        : String(raw);
    } catch {}
    throw new APIError(res.status, detail);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

const get   = (ep, a = true)           => request("GET",    ep, null, a);
const post  = (ep, b = null, a = true) => request("POST",   ep, b,    a);
const put   = (ep, b = null, a = true) => request("PUT",    ep, b,    a);
const patch = (ep, b = null, a = true) => request("PATCH",  ep, b,    a);
const del   = (ep, a = true)           => request("DELETE", ep, null, a);

// ──────────────────────────────────────────────────────────────
//  API pública
// ──────────────────────────────────────────────────────────────
window.API = {

  // ── Auth ──────────────────────────────────────────────────
  auth: {
    async login(email, password) {
      const data = await post("/auth/login", { email, password }, false);
      // Guardar tokens y arrancar timers via AuthModule
      AuthModule.setSession({ ...data, email });
      return data;
    },
    async refreshToken() {
      return AuthModule.getAccessToken();
    },
    logout: (reason) => AuthModule.logout(reason),
    isLoggedIn: () => AuthModule.isAuthenticated(),
    getTokenInfo: () => AuthModule.getTokenInfo(),
  },

  // ── Usuarios ──────────────────────────────────────────────
  usuarios: {
    listar:             ()            => get("/usuarios/"),
    crear:              (body)        => post("/usuarios/", body),
    darBaja:            (id)          => del(`/usuarios/${id}`),
    eliminar:           (id)          => del(`/usuarios/${id}/eliminar`),
    registrarBiometria: (id, b64)     => post(`/usuarios/${id}/biometria`, { imagen_base64: b64 }),
  },

  // ── Casilleros ────────────────────────────────────────────
  casilleros: {
    listar:         ()              => get("/casilleros/"),
    disponibles:    ()              => get("/casilleros/disponibles"),
    crear:          (body)          => post("/casilleros/", body),
    eliminar:       (id)            => del(`/casilleros/${id}`),
    cambiarEstado:  (id, estado)    => post(`/casilleros/${id}/estado`, { estado }),
    asignar:        (uid)           => post(`/casilleros/asignar/${uid}`),
    asignarManual:  (cid, uid)      => post(`/casilleros/${cid}/asignar/${uid}`),
    liberar:        (uid)           => del(`/casilleros/liberar/${uid}`),
    abrir:          (id)            => post(`/casilleros/${id}/abrir`),
  },

  // ── Accesos ───────────────────────────────────────────────
  accesos: {
    historial: (uid)  => get(`/accesos/historial/${uid}`),
    validar:   (body) => post("/accesos/validar", body, false),
  },

  // ── Reportes ──────────────────────────────────────────────
  reportes: {
    accesos:   (p = {}) => get("/reportes/accesos?"   + new URLSearchParams(p)),
    ocupacion: ()       => get("/reportes/ocupacion"),
  },

  // ── Hardware ──────────────────────────────────────────────
  hardware: {
    terminales:    ()             => get("/hardware/terminales"),
    controladores: ()             => get("/hardware/controladores"),
    ping:          (id)           => post(`/hardware/${id}/ping`),
    autorizar:     (id, valor)    => patch(`/hardware/terminales/${id}/autorizar`, { autorizado: valor }),
  },

  // ── Administradores ───────────────────────────────────────
  admin: {
    listar:       ()        => get("/admin/"),
    crear:        (body)    => post("/admin/", body),
    cambiarRol:   (id, rol) => patch(`/admin/${id}/rol`,    { rol }),
    toggleActivo: (id)      => patch(`/admin/${id}/activo`),
    me:           ()        => get("/admin/me"),
  },

  APIError,
};

// ──────────────────────────────────────────────────────────────
//  UI helpers
// ──────────────────────────────────────────────────────────────
window.showLoading = (id, msg = "Cargando...") => {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `
    <div class="text-center py-5 text-muted">
      <i class="fas fa-spinner fa-spin fa-2x mb-3 d-block"></i>
      <span style="font-size:14px;">${msg}</span>
    </div>`;
};

window.showError = (id, msg, onRetry = null) => {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `
    <div class="text-center py-5">
      <i class="fas fa-exclamation-triangle fa-2x text-danger mb-3 d-block"></i>
      <div style="font-size:14px;color:#dc3545;margin-bottom:12px;">${msg}</div>
      ${onRetry ? `<button class="btn btn-sm btn-outline-danger" onclick="(${onRetry})()">
        <i class="fas fa-redo mr-1"></i>Reintentar</button>` : ""}
    </div>`;
};

window.showEmpty = (id, msg = "Sin datos") => {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `
    <div class="text-center py-5 text-muted">
      <i class="fas fa-inbox fa-2x mb-3 d-block"></i>
      <span style="font-size:14px;">${msg}</span>
    </div>`;
};
