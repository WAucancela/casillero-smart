import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api/api.service';

interface Terminal {
  numero_serie: string;
  descripcion: string;
  ip_local: string;
  activo: boolean;
  piso: number;
  ultimo_contacto?: string;
}

interface Evento {
  id: number;
  timestamp: string;
  usuario: string;
  terminal_id: string;
  casillero_numero: string;
  confianza_biometrica?: number;
  resultado: string;
}

interface Contadores {
  total: number;
  exitosos: number;
  denegados: number;
  alertas: number;
}

@Component({
  selector: 'app-monitor',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule],
  templateUrl: './monitor.component.html',
  styleUrl: './monitor.component.css',
})
export class MonitorComponent implements OnInit, OnDestroy {

  // Terminales
  terminales: Terminal[]  = [];
  loadingTerminales = true;

  // Eventos stream
  eventos: Evento[]    = [];
  filtrados: Evento[]  = [];
  alertas: Evento[]    = [];
  ultimoEvento: Evento | null = null;

  // Filtros
  filtroTerminal  = '';
  filtroResultado = '';

  // Contadores
  contadores: Contadores = { total: 0, exitosos: 0, denegados: 0, alertas: 0 };

  // Estado stream
  paused     = false;
  ultimoPoll = '';
  newIds     = new Set<number>();
  maxId      = 0;

  private pollEventosId: ReturnType<typeof setInterval>    | null = null;
  private pollTerminalesId: ReturnType<typeof setInterval> | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargarTerminales();
    this.cargarEventos();
    this.pollTerminalesId = setInterval(() => this.cargarTerminales(), 15_000);
    this.pollEventosId    = setInterval(() => { if (!this.paused) this.cargarEventos(); }, 5_000);
  }

  ngOnDestroy(): void {
    if (this.pollEventosId)    clearInterval(this.pollEventosId);
    if (this.pollTerminalesId) clearInterval(this.pollTerminalesId);
  }

  // ── Terminales ─────────────────────────────────────────────

  cargarTerminales(): void {
    this.api.getTerminales().subscribe({
      next: (data) => { this.terminales = data; this.loadingTerminales = false; this.cdr.detectChanges(); },
      error: ()    => { this.loadingTerminales = false; this.cdr.detectChanges(); },
    });
  }

  get terminalesSelect(): { value: string; label: string }[] {
    return this.terminales.map(t => ({ value: t.numero_serie, label: `${t.numero_serie} (${t.ip_local})` }));
  }

  fmtContacto(ts?: string): string {
    if (!ts) return 'nunca';
    return new Date(ts).toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' });
  }

  // ── Eventos ────────────────────────────────────────────────

  cargarEventos(): void {
    const hoy       = new Date();
    const fechaHoy  = `${hoy.getFullYear()}-${String(hoy.getMonth()+1).padStart(2,'0')}-${String(hoy.getDate()).padStart(2,'0')}`;
    this.api.getReporteAccesos({ fecha_inicio: fechaHoy }).subscribe({
      next: (data: any) => {
        const todos: Evento[] = ([...(data.detalle ?? [])]).reverse();

        this.newIds.clear();
        todos.forEach(e => {
          if (e.id > this.maxId) { this.newIds.add(e.id); this.maxId = e.id; }
        });

        this.eventos = todos;
        this.contadores = {
          total:     data.resumen?.total_intentos ?? todos.length,
          exitosos:  data.resumen?.exitosos        ?? todos.filter((e: Evento) => e.resultado === 'exitoso').length,
          denegados: data.resumen?.denegados       ?? todos.filter((e: Evento) => e.resultado !== 'exitoso').length,
          alertas:   data.resumen?.denegados       ?? 0,
        };

        this.ultimoPoll = `Actualizado: ${new Date().toLocaleTimeString('es-EC')}`;
        this.aplicarFiltros();
        this.alertas      = todos.filter(e => e.resultado !== 'exitoso').slice(0, 10);
        this.ultimoEvento = todos[0] ?? null;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.ultimoPoll = `Error: ${err?.message ?? 'sin conexión'}`;
        this.cdr.detectChanges();
      },
    });
  }

  aplicarFiltros(): void {
    this.filtrados = this.eventos.filter(e => {
      if (this.filtroTerminal  && e.terminal_id !== this.filtroTerminal) return false;
      if (this.filtroResultado === 'exitoso'  && e.resultado !== 'exitoso') return false;
      if (this.filtroResultado === 'denegado' && e.resultado === 'exitoso') return false;
      return true;
    }).slice(0, 100);
  }

  // ── Controles ──────────────────────────────────────────────

  toggleStream(): void {
    this.paused = !this.paused;
    if (!this.paused) this.cargarEventos();
  }

  limpiarStream(): void {
    this.eventos       = [];
    this.filtrados     = [];
    this.alertas       = [];
    this.ultimoEvento  = null;
    this.newIds.clear();
    this.maxId         = 0;
    this.contadores    = { total: 0, exitosos: 0, denegados: 0, alertas: 0 };
  }

  // ── Helpers plantilla ──────────────────────────────────────

  get contadoresData() {
    return [
      { label: 'Total Eventos',   value: this.contadores.total,     color: 'secondary', icon: 'fa-stream'        },
      { label: 'Exitosos',        value: this.contadores.exitosos,   color: 'success',   icon: 'fa-check-circle'  },
      { label: 'Denegados',       value: this.contadores.denegados,  color: 'danger',    icon: 'fa-times-circle'  },
      { label: 'Alertas Activas', value: this.contadores.alertas,    color: 'warning',   icon: 'fa-bell'          },
    ];
  }

  isNuevo(e: Evento): boolean { return this.newIds.has(e.id); }

  resultadoBadge(resultado: string): { text: string; cls: string } {
    return resultado === 'exitoso'
      ? { text: 'Exitoso',  cls: 'badge-success' }
      : { text: resultado.replace(/_/g, ' '), cls: 'badge-danger' };
  }

  confianzaColor(val?: number): string {
    if (val == null) return 'secondary';
    if (val >= 0.8) return 'success';
    if (val >= 0.6) return 'warning';
    return 'danger';
  }

  confianzaPct(val?: number): string {
    return val != null ? `${Math.round(val * 100)}%` : '—';
  }

  fmtHora(ts: string): string {
    if (!ts) return '—';
    return new Date(ts).toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
