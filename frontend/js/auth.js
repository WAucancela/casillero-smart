// ══════════════════════════════════════════════════════════════
//  auth.js — Módulo completo de autenticación JWT
//
//  Responsabilidades:
//    · Guardar / leer / borrar tokens (access + refresh)
//    · Decodificar el JWT localmente (sin llamada al servidor)
//    · Verificar expiración antes de cada request
//    · Renovar el access token automáticamente con refresh token
//    · Guard de ruta: bloquear acceso a páginas protegidas
//    · Detectar inactividad y cerrar sesión automáticamente
//    · Sincronizar logout entre tabs del mismo navegador
// ══════════════════════════════════════════════════════════════

const AUTH_CONFIG = {
  accessKey:        "cas_access_token",
  refreshKey:       "cas_refresh_token",
  emailKey:         "cas_admin_email",
  nombreKey:        "cas_admin_nombre",
  // Cuántos segundos antes de la expiración se intenta renovar
  refreshMarginSec: 60,
  // Minutos de inactividad antes de cerrar sesión automáticamente
  inactivityMinutes: 30,
  loginPage:        "login.html",
};

// ──────────────────────────────────────────────────────────────
//  Decodificador JWT local (sin librería externa)
//  Solo decodifica el payload; NO verifica la firma.
//  La verificación de firma es responsabilidad del backend.
// ──────────────────────────────────────────────────────────────
function decodeJWT(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    // Base64url → Base64 → JSON
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(payload).split("").map(c =>
        "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)
      ).join("")
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function tokenExpiresAt(token) {
  const payload = decodeJWT(token);
  return payload?.exp ? payload.exp * 1000 : 0;  // ms
}

function tokenIsExpired(token) {
  const exp = tokenExpiresAt(token);
  if (!exp) return true;
  return Date.now() >= exp;
}

function tokenExpiresInSec(token) {
  const exp = tokenExpiresAt(token);
  return Math.max(0, Math.floor((exp - Date.now()) / 1000));
}

// ──────────────────────────────────────────────────────────────
//  Almacenamiento
// ──────────────────────────────────────────────────────────────
const TokenStore = {
  setTokens(access, refresh) {
    localStorage.setItem(AUTH_CONFIG.accessKey,  access);
    localStorage.setItem(AUTH_CONFIG.refreshKey, refresh);
  },
  getAccess()  { return localStorage.getItem(AUTH_CONFIG.accessKey);  },
  getRefresh() { return localStorage.getItem(AUTH_CONFIG.refreshKey); },
  setProfile(email, nombre) {
    localStorage.setItem(AUTH_CONFIG.emailKey,  email);
    localStorage.setItem(AUTH_CONFIG.nombreKey, nombre || email);
  },
  getEmail()  { return localStorage.getItem(AUTH_CONFIG.emailKey)  || ""; },
  getNombre() { return localStorage.getItem(AUTH_CONFIG.nombreKey) || ""; },
  clear() {
    [AUTH_CONFIG.accessKey, AUTH_CONFIG.refreshKey,
     AUTH_CONFIG.emailKey,  AUTH_CONFIG.nombreKey].forEach(k =>
       localStorage.removeItem(k)
    );
  },
  hasTokens() {
    return !!(this.getAccess() && this.getRefresh());
  },
};

// ──────────────────────────────────────────────────────────────
//  Renovación automática del access token
// ──────────────────────────────────────────────────────────────
let _refreshTimer  = null;
let _refreshLock   = false;   // evita llamadas concurrentes

async function doRefresh() {
  if (_refreshLock) return TokenStore.getAccess();
  _refreshLock = true;

  const refreshToken = TokenStore.getRefresh();
  if (!refreshToken || tokenIsExpired(refreshToken)) {
    _refreshLock = false;
    AuthModule.logout("session_expired");
    return null;
  }

  try {
    const base = window.API_BASE_URL || "/api";
    const res  = await fetch(`${base}/auth/refresh`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      _refreshLock = false;
      AuthModule.logout("session_expired");
      return null;
    }

    const data = await res.json();
    TokenStore.setTokens(data.access_token, data.refresh_token || refreshToken);
    _refreshLock = false;
    scheduleRefresh();
    return data.access_token;
  } catch {
    _refreshLock = false;
    // Sin conexión: no cerrar sesión, dejar que el próximo request falle
    return TokenStore.getAccess();
  }
}

function scheduleRefresh() {
  if (_refreshTimer) clearTimeout(_refreshTimer);
  const token = TokenStore.getAccess();
  if (!token) return;

  const secsLeft = tokenExpiresInSec(token);
  const delay    = Math.max(0, (secsLeft - AUTH_CONFIG.refreshMarginSec) * 1000);

  _refreshTimer = setTimeout(() => {
    doRefresh();
  }, delay);
}

// ──────────────────────────────────────────────────────────────
//  Obtener un access token válido (renovando si hace falta)
// ──────────────────────────────────────────────────────────────
async function getValidAccessToken() {
  const token = TokenStore.getAccess();
  if (!token) return null;

  // Si expira en menos de 60 s → renovar ahora
  if (tokenExpiresInSec(token) < AUTH_CONFIG.refreshMarginSec) {
    return doRefresh();
  }

  return token;
}

// ──────────────────────────────────────────────────────────────
//  Detector de inactividad
// ──────────────────────────────────────────────────────────────
let _inactivityTimer = null;

function resetInactivityTimer() {
  if (_inactivityTimer) clearTimeout(_inactivityTimer);
  _inactivityTimer = setTimeout(() => {
    AuthModule.logout("inactivity");
  }, AUTH_CONFIG.inactivityMinutes * 60 * 1000);
}

function startInactivityWatcher() {
  ["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(evt =>
    document.addEventListener(evt, resetInactivityTimer, { passive: true })
  );
  resetInactivityTimer();
}

function stopInactivityWatcher() {
  if (_inactivityTimer) clearTimeout(_inactivityTimer);
  ["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(evt =>
    document.removeEventListener(evt, resetInactivityTimer)
  );
}

// ──────────────────────────────────────────────────────────────
//  Sincronización de logout entre tabs (StorageEvent)
// ──────────────────────────────────────────────────────────────
window.addEventListener("storage", (e) => {
  if (e.key === AUTH_CONFIG.accessKey && !e.newValue) {
    // Otro tab borró el token → redirigir aquí también
    const isLoginPage = window.location.pathname.endsWith("login.html");
    if (!isLoginPage) {
      window.location.href = AUTH_CONFIG.loginPage + "?reason=logout_other_tab";
    }
  }
});

// ──────────────────────────────────────────────────────────────
//  Módulo público: AuthModule
// ──────────────────────────────────────────────────────────────
const AuthModule = {

  // Guardar tokens después del login exitoso
  setSession(data) {
    TokenStore.setTokens(data.access_token, data.refresh_token);
    const payload = decodeJWT(data.access_token);
    TokenStore.setProfile(
      payload?.email || data.email || "",
      payload?.nombre || data.nombre || ""
    );
    scheduleRefresh();
    startInactivityWatcher();
  },

  // Cerrar sesión (local + opcionalmente notificar al backend)
  logout(reason = "manual") {
    if (_refreshTimer)    clearTimeout(_refreshTimer);
    stopInactivityWatcher();
    TokenStore.clear();

    const params = new URLSearchParams();
    if (reason !== "manual") params.set("reason", reason);
    const suffix = params.toString() ? `?${params}` : "";
    window.location.href = AUTH_CONFIG.loginPage + suffix;
  },

  // Verificar sesión activa con token válido (uso en guard)
  async isAuthenticated() {
    if (!TokenStore.hasTokens()) return false;
    const token = await getValidAccessToken();
    return !!token;
  },

  // Obtener token listo para Authorization header
  getAccessToken: getValidAccessToken,

  // Perfil del usuario autenticado
  getEmail:  TokenStore.getEmail.bind(TokenStore),
  getNombre: TokenStore.getNombre.bind(TokenStore),

  // Info del token actual (para depuración / UI)
  getTokenInfo() {
    const token = TokenStore.getAccess();
    if (!token) return null;
    const payload = decodeJWT(token);
    return {
      email:       payload?.email,
      sub:         payload?.sub,
      exp:         payload?.exp,
      expiresAt:   new Date(tokenExpiresAt(token)).toLocaleString("es-EC"),
      expiresInSec: tokenExpiresInSec(token),
      expired:      tokenIsExpired(token),
    };
  },

  // Inicializar en páginas protegidas
  init() {
    scheduleRefresh();
    startInactivityWatcher();
  },
};

// ──────────────────────────────────────────────────────────────
//  Guard de ruta — reemplaza requireAuth()
//  Uso: await guardRoute();   (al inicio de cada página protegida)
// ──────────────────────────────────────────────────────────────
window.guardRoute = async function() {
  const ok = await AuthModule.isAuthenticated();
  if (!ok) {
    const here = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `${AUTH_CONFIG.loginPage}?next=${here}`;
    return false;
  }
  AuthModule.init();
  return true;
};

// Mantener compatibilidad con el requireAuth() sincrónico anterior
// (redirige sin await — úsalo solo si no puedes usar await)
window.requireAuth = function() {
  const token = TokenStore.getAccess();
  if (!token || tokenIsExpired(token)) {
    const here = encodeURIComponent(window.location.pathname);
    window.location.href = `${AUTH_CONFIG.loginPage}?next=${here}`;
    return false;
  }
  AuthModule.init();
  return true;
};

window.AuthModule = AuthModule;
