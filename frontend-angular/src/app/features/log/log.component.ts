import { Component, OnInit } from '@angular/core';
import { NgIf, NgFor, NgClass, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api/api.service';

interface LogEntry {
  id: number;
  timestamp: string;
  usuario: string;
  departamento: string;
  terminal_id: string;
  casillero_numero: string | number;
  confianza_biometrica: number | null;
  resultado: string;
}

@Component({
  selector: 'app-log',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule],
  templateUrl: './log.component.html',
  styleUrl: './log.component.css',
})
export class LogComponent implements OnInit {

  loading = false;
  error   = '';

  // Datos
  todos:    LogEntry[] = [];
  filtrados: LogEntry[] = [];

  // Filtros
  fechaDesde  = '';
  fechaHasta  = '';
  busqueda    = '';
  filtroResultado = '';
  filtroTerminal  = '';

  // Paginación
  readonly PAGE_SIZE = 25;
  pagina    = 1;
  totalPags = 1;

  // Terminales disponibles en los datos
  terminalesDisponibles: string[] = [];

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    const hoy   = new Date();
    const desde = new Date(Date.now() - 30 * 24 * 3_600_000);
    this.fechaHasta = hoy.toISOString().slice(0, 10);
    this.fechaDesde = desde.toISOString().slice(0, 10);
    this.cargar();
  }

  // ── Carga ──────────────────────────────────────────────────────

  cargar(): void {
    this.loading = true;
    this.error   = '';
    this.api.getReporteAccesos({ fecha_inicio: this.fechaDesde, fecha_fin: this.fechaHasta })
      .subscribe({
        next: (res) => {
          this.todos = (res.detalle ?? []) as LogEntry[];
          this.extraerTerminales();
          this.aplicarFiltros();
          this.loading = false;
        },
        error: (err) => {
          this.error   = err?.error?.detail ?? 'Error al cargar el log.';
          this.loading = false;
        },
      });
  }

  // ── Filtros ────────────────────────────────────────────────────

  private extraerTerminales(): void {
    const set = new Set<string>();
    this.todos.forEach(e => { if (e.terminal_id) set.add(e.terminal_id); });
    this.terminalesDisponibles = Array.from(set).sort();
  }

  aplicarFiltros(): void {
    const q   = this.busqueda.toLowerCase().trim();
    let rows  = this.todos;

    if (q) {
      rows = rows.filter(e =>
        (e.usuario        ?? '').toLowerCase().includes(q) ||
        (e.departamento   ?? '').toLowerCase().includes(q) ||
        String(e.casillero_numero ?? '').includes(q)
      );
    }
    if (this.filtroResultado) {
      rows = rows.filter(e => e.resultado === this.filtroResultado);
    }
    if (this.filtroTerminal) {
      rows = rows.filter(e => e.terminal_id === this.filtroTerminal);
    }

    this.filtrados = rows;
    this.totalPags = Math.max(1, Math.ceil(rows.length / this.PAGE_SIZE));
    this.pagina    = 1;
  }

  limpiarFiltros(): void {
    this.busqueda        = '';
    this.filtroResultado = '';
    this.filtroTerminal  = '';
    this.aplicarFiltros();
  }

  // ── Paginación ─────────────────────────────────────────────────

  get paginaActual(): LogEntry[] {
    const start = (this.pagina - 1) * this.PAGE_SIZE;
    return this.filtrados.slice(start, start + this.PAGE_SIZE);
  }

  get paginas(): number[] {
    const total = this.totalPags;
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    // ventana de 5 alrededor de la página actual
    const start = Math.max(1, Math.min(this.pagina - 2, total - 4));
    return Array.from({ length: Math.min(5, total) }, (_, i) => start + i);
  }

  irA(p: number): void {
    if (p >= 1 && p <= this.totalPags) this.pagina = p;
  }

  // ── Exportar CSV ────────────────────────────────────────────────

  exportCSV(): void {
    const cols = ['ID', 'Fecha', 'Hora', 'Usuario', 'Departamento', 'Terminal', 'Casillero', 'Confianza', 'Resultado'];
    const rows = this.filtrados.map(e => [
      e.id,
      e.timestamp?.slice(0, 10) ?? '',
      e.timestamp?.slice(11, 19) ?? '',
      e.usuario       ?? '',
      e.departamento  ?? '',
      e.terminal_id   ?? '',
      e.casillero_numero ?? '',
      e.confianza_biometrica != null ? `${Math.round(e.confianza_biometrica * 100)}%` : '',
      e.resultado,
    ]);
    const csv = [cols, ...rows].map(r => r.join(',')).join('\n');
    const a   = document.createElement('a');
    a.href    = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = `log_accesos_${this.fechaDesde}_${this.fechaHasta}.csv`;
    a.click();
  }

  // ── Helpers ────────────────────────────────────────────────────

  fmtFecha(ts: string): string {
    if (!ts) return '—';
    return ts.slice(0, 10);
  }

  fmtHora(ts: string): string {
    if (!ts) return '—';
    return ts.slice(11, 19);
  }

  resultadoBadge(r: string): { cls: string; text: string } {
    return r === 'exitoso'
      ? { cls: 'badge-success', text: 'Exitoso' }
      : { cls: 'badge-danger',  text: r?.replace('_', ' ') ?? 'Denegado' };
  }

  confianzaPct(c: number | null): string {
    if (c == null) return '—';
    return `${Math.round(c * 100)}%`;
  }

  confianzaColor(c: number | null): string {
    if (c == null) return 'secondary';
    if (c >= 0.85) return 'success';
    if (c >= 0.65) return 'warning';
    return 'danger';
  }

  rangoFin(): number {
    return Math.min(this.pagina * this.PAGE_SIZE, this.filtrados.length);
  }

  get resumenFiltros(): string {
    const partes: string[] = [];
    if (this.filtroResultado) partes.push(this.filtroResultado === 'exitoso' ? 'solo exitosos' : 'solo denegados');
    if (this.filtroTerminal)  partes.push(`terminal: ${this.filtroTerminal}`);
    if (this.busqueda)        partes.push(`"${this.busqueda}"`);
    return partes.length ? partes.join(' · ') : '';
  }
}
