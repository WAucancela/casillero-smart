"""
Casilleros - Launcher
Levanta el sistema completo con Docker Compose
"""
import os
import sys
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# ── Directorio base del proyecto ──────────────────────────────────────────────
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

COMPOSE_CMD = [
    "docker", "compose",
    "-f", str(BASE_DIR / "docker-compose.yml"),
    "-f", str(BASE_DIR / "docker-compose.dev.yml"),
]

APP_URL = "http://localhost"
BACKEND_URL = "http://localhost:8000/health"


# ── Helpers ───────────────────────────────────────────────────────────────────
def docker_running() -> bool:
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=8)
        return r.returncode == 0
    except Exception:
        return False


def services_up() -> bool:
    try:
        r = subprocess.run(
            COMPOSE_CMD + ["ps", "--services", "--filter", "status=running"],
            capture_output=True, text=True, timeout=10, cwd=BASE_DIR
        )
        return "backend" in r.stdout
    except Exception:
        return False


# ── Ventana principal ─────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Casilleros — Launcher")
        self.resizable(False, False)
        self.configure(bg="#1e2a4a")
        self._center()
        self._build_ui()
        self._process = None
        self._running = False

    def _center(self):
        self.geometry("480x340")
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 480) // 2
        y = (self.winfo_screenheight() - 340) // 2
        self.geometry(f"480x340+{x}+{y}")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg="#0d3060", pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔒  CASILLEROS AUTOMATIZADOS",
                 font=("Consolas", 15, "bold"), bg="#0d3060", fg="white").pack()
        tk.Label(hdr, text="Sistema de gestión v1.0",
                 font=("Segoe UI", 9), bg="#0d3060", fg="#7a9cc8").pack()

        # Estado Docker
        self.frm_estado = tk.Frame(self, bg="#1e2a4a", pady=12)
        self.frm_estado.pack(fill="x", padx=30)

        tk.Label(self.frm_estado, text="Estado Docker:",
                 font=("Segoe UI", 10), bg="#1e2a4a", fg="#a0b4cc").grid(row=0, column=0, sticky="w")
        self.lbl_docker = tk.Label(self.frm_estado, text="Verificando...",
                                   font=("Segoe UI", 10, "bold"), bg="#1e2a4a", fg="#ffc107")
        self.lbl_docker.grid(row=0, column=1, padx=10, sticky="w")

        tk.Label(self.frm_estado, text="Servicios:",
                 font=("Segoe UI", 10), bg="#1e2a4a", fg="#a0b4cc").grid(row=1, column=0, sticky="w")
        self.lbl_srv = tk.Label(self.frm_estado, text="—",
                                font=("Segoe UI", 10, "bold"), bg="#1e2a4a", fg="#6c757d")
        self.lbl_srv.grid(row=1, column=1, padx=10, sticky="w")

        # Log
        tk.Label(self, text="Log:", font=("Segoe UI", 9),
                 bg="#1e2a4a", fg="#a0b4cc", anchor="w").pack(fill="x", padx=30)

        self.txt = tk.Text(self, height=7, font=("Consolas", 8),
                           bg="#0f1623", fg="#a8d8a8", relief="flat",
                           state="disabled", wrap="word")
        self.txt.pack(fill="x", padx=30, pady=(0, 10))

        # Barra de progreso
        self.progress = ttk.Progressbar(self, mode="indeterminate", length=420)
        self.progress.pack(pady=(0, 8))

        # Botones
        frm_btns = tk.Frame(self, bg="#1e2a4a")
        frm_btns.pack()

        self.btn_start = tk.Button(frm_btns, text="▶  Levantar sistema",
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#007bff", fg="white", relief="flat",
                                   padx=18, pady=8, cursor="hand2",
                                   command=self._on_start)
        self.btn_start.grid(row=0, column=0, padx=6)

        self.btn_stop = tk.Button(frm_btns, text="■  Detener",
                                  font=("Segoe UI", 10), state="disabled",
                                  bg="#dc3545", fg="white", relief="flat",
                                  padx=18, pady=8, cursor="hand2",
                                  command=self._on_stop)
        self.btn_stop.grid(row=0, column=1, padx=6)

        self.btn_browser = tk.Button(frm_btns, text="🌐  Abrir sistema",
                                     font=("Segoe UI", 10), state="disabled",
                                     bg="#28a745", fg="white", relief="flat",
                                     padx=18, pady=8, cursor="hand2",
                                     command=lambda: webbrowser.open(APP_URL))
        self.btn_browser.grid(row=0, column=2, padx=6)

        # Verificar Docker al iniciar
        threading.Thread(target=self._check_docker, daemon=True).start()

    # ── Log ───────────────────────────────────────────────────────────────────
    def _log(self, msg: str, color: str = "#a8d8a8"):
        def _write():
            self.txt.configure(state="normal")
            self.txt.insert("end", msg + "\n")
            self.txt.see("end")
            self.txt.configure(state="disabled")
        self.after(0, _write)

    # ── Verificar Docker ──────────────────────────────────────────────────────
    def _check_docker(self):
        ok = docker_running()
        def _upd():
            if ok:
                self.lbl_docker.config(text="✔ Corriendo", fg="#28a745")
                # Verificar si ya hay servicios levantados
                if services_up():
                    self._mark_running()
                    self._log("Servicios ya están corriendo.")
            else:
                self.lbl_docker.config(text="✘ No disponible", fg="#dc3545")
                self._log("Docker Desktop no está corriendo.", "#ff6b6b")
                self._log("Ábrelo y luego presiona 'Levantar sistema'.", "#ffc107")
        self.after(0, _upd)

    # ── Levantar ──────────────────────────────────────────────────────────────
    def _on_start(self):
        if not docker_running():
            messagebox.showerror("Docker no disponible",
                                 "Docker Desktop no está corriendo.\nÁbrelo e inténtalo de nuevo.")
            return

        self.btn_start.config(state="disabled")
        self.progress.start(12)
        self._log("Levantando servicios...")
        threading.Thread(target=self._start_services, daemon=True).start()

    def _start_services(self):
        try:
            cmd = COMPOSE_CMD + ["up", "--build", "-d"]
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=BASE_DIR
            )
            for line in self._process.stdout:
                line = line.rstrip()
                if line:
                    self._log(line)

            self._process.wait()

            if self._process.returncode == 0:
                self._log("✔ Servicios levantados correctamente.", "#28a745")
                self.after(0, self._mark_running)
                self.after(2000, lambda: webbrowser.open(APP_URL))
            else:
                self._log("✘ Error al levantar servicios.", "#ff6b6b")
                self.after(0, lambda: self.btn_start.config(state="normal"))
        except Exception as e:
            self._log(f"Error: {e}", "#ff6b6b")
            self.after(0, lambda: self.btn_start.config(state="normal"))
        finally:
            self.after(0, self.progress.stop)

    def _mark_running(self):
        self._running = True
        self.lbl_srv.config(text="✔ En línea", fg="#28a745")
        self.btn_stop.config(state="normal")
        self.btn_browser.config(state="normal")
        self.btn_start.config(state="disabled")
        self.progress.stop()

    # ── Detener ───────────────────────────────────────────────────────────────
    def _on_stop(self):
        if not messagebox.askyesno("Detener sistema",
                                   "¿Deseas detener todos los servicios?"):
            return
        self.btn_stop.config(state="disabled")
        self.btn_browser.config(state="disabled")
        self.progress.start(12)
        self._log("Deteniendo servicios...")
        threading.Thread(target=self._stop_services, daemon=True).start()

    def _stop_services(self):
        try:
            subprocess.run(COMPOSE_CMD + ["down"],
                           cwd=BASE_DIR, timeout=60)
            self._log("✔ Servicios detenidos.", "#ffc107")
            self.after(0, self._mark_stopped)
        except Exception as e:
            self._log(f"Error al detener: {e}", "#ff6b6b")
        finally:
            self.after(0, self.progress.stop)

    def _mark_stopped(self):
        self._running = False
        self.lbl_srv.config(text="✘ Detenido", fg="#dc3545")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.btn_browser.config(state="disabled")

    # ── Cerrar ventana ────────────────────────────────────────────────────────
    def on_close(self):
        if self._running:
            if not messagebox.askyesno("Cerrar",
                                       "Los servicios siguen corriendo.\n¿Cerrar el launcher? (Los servicios continuarán en segundo plano)"):
                return
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
