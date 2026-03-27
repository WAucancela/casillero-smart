// layout.js — Genera sidebar y navbar comunes con control de roles
window.renderLayout = function(paginaActiva) {
  // Leer rol del JWT decodificado
  const tokenInfo = (typeof AuthModule !== "undefined") ? AuthModule.getTokenInfo() : null;
  const token     = tokenInfo ? localStorage.getItem("cas_access_token") : null;
  let rol = "viewer";
  if (token) {
    try {
      const parts   = token.split(".");
      const payload = JSON.parse(atob(parts[1].replace(/-/g,"+").replace(/_/g,"/")));
      rol = payload.rol || "viewer";
    } catch {}
  }

  const esSuperadmin = rol === "superadmin";
  const esAdmin      = rol === "superadmin" || rol === "admin";
  const esViewer     = true; // todos los roles válidos ven lo básico

  const nav = [
    { id:"dashboard",       label:"Dashboard",       icon:"fa-tachometer-alt", href:"dashboard.html",       visible: esViewer   },
    { id:"usuarios",        label:"Usuarios",         icon:"fa-users",          href:"usuarios.html",        visible: esViewer   },
    { id:"casilleros",      label:"Casilleros",       icon:"fa-boxes",          href:"casilleros.html",      visible: esViewer   },
    { id:"monitor",         label:"Monitor",          icon:"fa-broadcast-tower",href:"monitor.html",         visible: esViewer,
      badge:{text:"LIVE", cls:"badge-success"} },
    { id:"reportes",        label:"Reportes",         icon:"fa-chart-bar",      href:"reportes.html",        visible: esAdmin    },
    { id:"log",             label:"Log Completo",     icon:"fa-list-alt",       href:"log.html",             visible: esAdmin    },
    { id:"hardware",        label:"Hardware",         icon:"fa-microchip",      href:"hardware.html",        visible: esSuperadmin },
    { id:"administradores", label:"Administradores",  icon:"fa-user-shield",    href:"administradores.html", visible: esSuperadmin },
  ];

  const nombre = AuthModule ? AuthModule.getNombre() : "";
  const email  = AuthModule ? AuthModule.getEmail()  : (localStorage.getItem("cas_admin_email") || "");

  // Etiqueta de rol en español
  const rolLabels = { superadmin: "Super Usuario", admin: "Jefatura", viewer: "Operador" };
  const rolLabel  = rolLabels[rol] || rol;

  // Sidebar items
  document.getElementById("sidebar-nav").innerHTML = nav
    .filter(n => n.visible)
    .map(n => `
    <li class="nav-item">
      <a href="${n.href}" class="nav-link ${n.id === paginaActiva ? 'active' : ''}">
        <i class="nav-icon fas ${n.icon}"></i>
        <p>${n.label}${n.badge ? `<span class="badge ${n.badge.cls} right" style="font-size:9px;">${n.badge.text}</span>` : ""}</p>
      </a>
    </li>`).join("");

  // Nombre/email en sidebar
  const emailEl  = document.getElementById("sidebar-email");
  const nombreEl = document.getElementById("sidebar-nombre");
  const rolEl    = document.getElementById("sidebar-rol");
  if (emailEl)  emailEl.textContent  = email;
  if (nombreEl) nombreEl.textContent = nombre || email;
  if (rolEl)    rolEl.textContent    = rolLabel;

  // Rol badge en navbar si existe
  const navRolEl = document.getElementById("navbar-rol");
  if (navRolEl) {
    navRolEl.textContent = rolLabel;
    navRolEl.className   = `badge badge-${esSuperadmin ? "danger" : esAdmin ? "warning" : "secondary"}`;
  }

  // Logout
  document.querySelectorAll(".btn-logout").forEach(b => b.addEventListener("click", () => {
    if (typeof AuthModule !== "undefined") {
      AuthModule.logout("manual");
    } else {
      localStorage.clear();
      window.location.href = "login.html";
    }
  }));
};
