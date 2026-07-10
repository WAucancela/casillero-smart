// ══════════════════════════════════════════════════════
//  shared.js — Datos mock, utilidades y funciones comunes
//  Reemplazar las funciones fetchAPI() con llamadas reales
// ══════════════════════════════════════════════════════

// ── Constantes globales ────────────────────────────────
const RESULTADOS_TIPOS = ["exitoso","denegado_biometria","denegado_usuario_inactivo","denegado_fuera_horario"];
const TERMINALES_IDS   = ["term-p1-entrada","term-p2-entrada","term-p3-entrada"];
const DEPARTAMENTOS    = ["Tecnología","Finanzas","RRHH","Marketing","Operaciones"];

// ── Mock: Usuarios ─────────────────────────────────────
window.MOCK_USUARIOS = [
  { id:1, nombre:"Ana",    apellido:"García",    email:"ana.garcia@empresa.com",    departamento:"Tecnología", piso_preferido:3, estado:"activo",              casillero:"A3-012" },
  { id:2, nombre:"Carlos", apellido:"López",     email:"carlos.lopez@empresa.com",  departamento:"Finanzas",   piso_preferido:2, estado:"activo",              casillero:"B2-047" },
  { id:3, nombre:"María",  apellido:"Martínez",  email:"maria.martinez@empresa.com",departamento:"RRHH",       piso_preferido:1, estado:"pendiente_biometria", casillero:null     },
  { id:4, nombre:"Pedro",  apellido:"Sánchez",   email:"pedro.sanchez@empresa.com", departamento:"Marketing",  piso_preferido:2, estado:"activo",              casillero:"B2-033" },
  { id:5, nombre:"Lucía",  apellido:"Fernández", email:"lucia.fernandez@empresa.com",departamento:"Tecnología",piso_preferido:3, estado:"inactivo",            casillero:null     },
  { id:6, nombre:"Diego",  apellido:"Torres",    email:"diego.torres@empresa.com",  departamento:"Operaciones",piso_preferido:1, estado:"activo",              casillero:"A1-005" },
];

// ── Mock: Controladores ────────────────────────────────
window.MOCK_CONTROLADORES = [
  { id:"ctrl-p1-a", descripcion:"Piso 1 Zona A", piso:1, zona:"A", ip_local:"192.168.1.10", activo:true },
  { id:"ctrl-p1-b", descripcion:"Piso 1 Zona B", piso:1, zona:"B", ip_local:"192.168.1.11", activo:true },
  { id:"ctrl-p2-a", descripcion:"Piso 2 Zona A", piso:2, zona:"A", ip_local:"192.168.1.20", activo:true },
  { id:"ctrl-p2-b", descripcion:"Piso 2 Zona B", piso:2, zona:"B", ip_local:"192.168.1.21", activo:false},
  { id:"ctrl-p3-a", descripcion:"Piso 3 Zona A", piso:3, zona:"A", ip_local:"192.168.1.30", activo:true },
];

// ── Mock: Casilleros ───────────────────────────────────
window.MOCK_CASILLEROS = (function() {
  const estados = ["libre","ocupado","libre","libre","bloqueado","libre","libre","mantenimiento"];
  const list = [];
  let num = 1;
  window.MOCK_CONTROLADORES.forEach(ctrl => {
    for (let p = 1; p <= 25; p++) {
      const estado = estados[num % estados.length];
      const usuario = estado === "ocupado"
        ? MOCK_USUARIOS[num % MOCK_USUARIOS.length]
        : null;
      list.push({
        id: num,
        numero: `${ctrl.zona}${ctrl.piso}-${String(p).padStart(3,"0")}`,
        piso: ctrl.piso,
        zona: ctrl.zona,
        controlador_id: ctrl.id,
        puerto_controlador: (p % 8) + 1,
        estado,
        usuario_asignado_id:   usuario ? usuario.id   : null,
        usuario_asignado_nombre: usuario ? `${usuario.nombre} ${usuario.apellido}` : null,
      });
      num++;
    }
  });
  return list;
})();

// ── Mock: Terminales ───────────────────────────────────
window.MOCK_TERMINALES = [
  { id:"term-p1-entrada", descripcion:"Terminal Piso 1", piso:1, ubicacion:"Pasillo principal P1", ip_local:"192.168.1.50", activo:true,  ultimo_ping: new Date() },
  { id:"term-p2-entrada", descripcion:"Terminal Piso 2", piso:2, ubicacion:"Pasillo principal P2", ip_local:"192.168.1.51", activo:true,  ultimo_ping: new Date() },
  { id:"term-p3-entrada", descripcion:"Terminal Piso 3", piso:3, ubicacion:"Pasillo principal P3", ip_local:"192.168.1.52", activo:false, ultimo_ping: new Date(Date.now() - 3600000) },
];

// ── Mock: Logs ─────────────────────────────────────────
window.generarLogs = function(n = 150) {
  const logs = [];
  const nombres = MOCK_USUARIOS.map(u => `${u.nombre} ${u.apellido}`);
  const casNros  = MOCK_CASILLEROS.filter(c => c.estado === "ocupado").map(c => c.numero);
  for (let i = 1; i <= n; i++) {
    const r   = RESULTADOS_TIPOS[Math.floor(Math.random() * RESULTADOS_TIPOS.length)];
    const usr = r === "denegado_biometria" ? "Desconocido"
              : nombres[Math.floor(Math.random() * (nombres.length - 1))];
    const uObj = MOCK_USUARIOS.find(u => `${u.nombre} ${u.apellido}` === usr);
    logs.push({
      id: i,
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 3600000),
      usuario:      usr,
      usuario_id:   uObj ? uObj.id : null,
      departamento: uObj ? uObj.departamento : "—",
      terminal:     TERMINALES_IDS[Math.floor(Math.random() * 3)],
      casillero:    r === "exitoso" && casNros.length ? casNros[Math.floor(Math.random() * casNros.length)] : null,
      resultado:    r,
      confianza:    r === "exitoso"
        ? (0.75 + Math.random() * 0.25).toFixed(3)
        : (Math.random() * 0.74).toFixed(3),
    });
  }
  return logs.sort((a, b) => b.timestamp - a.timestamp);
};

window.MOCK_LOGS = window.generarLogs(150);

// ── Escapado de HTML (previene XSS al interpolar datos del servidor) ──
window.escapeHtml = function(str) {
  if (str === null || str === undefined) return "";
  return String(str).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
};

// ── Utilidades de formato ──────────────────────────────
window.fmtFecha = d => new Date(d).toLocaleDateString("es-EC",{day:"2-digit",month:"short",year:"numeric"});
window.fmtHora  = d => new Date(d).toLocaleTimeString("es-EC",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
window.fmtFechaCorta = d => new Date(d).toLocaleDateString("es-EC",{day:"2-digit",month:"short"});

window.estadoColor = {
  activo:              "success",
  pendiente_biometria: "warning",
  inactivo:            "secondary",
  libre:               "success",
  ocupado:             "primary",
  bloqueado:           "danger",
  mantenimiento:       "warning",
};

window.estadoIcon = {
  activo:              "fa-check-circle",
  pendiente_biometria: "fa-clock",
  inactivo:            "fa-ban",
  libre:               "fa-lock-open",
  ocupado:             "fa-lock",
  bloqueado:           "fa-minus-circle",
  mantenimiento:       "fa-tools",
};

window.resultadoBadge = r => r === "exitoso"
  ? `<span class="badge" style="background:#d4edda;color:#155724;">✓ Exitoso</span>`
  : `<span class="badge" style="background:#f8d7da;color:#721c24;">✗ ${r.replace(/_/g," ")}</span>`;

window.confianzaHtml = v => {
  const n = parseFloat(v);
  const cls = n >= 0.75 ? "text-success" : "text-danger";
  return `<span class="mono ${cls} font-weight-bold">${v}</span>`;
};

// ── Reloj en navbar ────────────────────────────────────
window.iniciarReloj = function() {
  const el = document.getElementById("reloj");
  if (!el) return;
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString("es-EC",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
  };
  tick();
  setInterval(tick, 1000);
};

// ── Toast notification ─────────────────────────────────
window.toast = function(msg, type = "success") {
  const div = document.createElement("div");
  div.className = `alert alert-${type} alert-dismissible fade show`;
  div.style.cssText = "position:fixed;top:70px;right:20px;z-index:9999;min-width:280px;box-shadow:0 4px 12px rgba(0,0,0,0.15);";
  div.innerHTML = `${msg}<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>`;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3500);
};

// ── API helper (para cuando conectes el backend real) ──
window.fetchAPI = async function(endpoint, options = {}) {
  // Descomentar cuando el backend esté disponible:
  // const res = await fetch(API_BASE + endpoint, {
  //   headers: { "Authorization": `Bearer ${localStorage.getItem("token")}`, "Content-Type": "application/json" },
  //   ...options
  // });
  // if (!res.ok) throw new Error(await res.text());
  // return res.json();
  console.log(`[mock] fetchAPI: ${endpoint}`, options);
  return null; // Mock: retorna null, cada módulo usa MOCK_*
};
