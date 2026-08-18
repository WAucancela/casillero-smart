import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api/api.service';

interface Terminal {
  id: number;
  numero_serie: string;
  descripcion: string;
  ip_local: string;
  piso: number;
  activo: boolean;
  ultimo_contacto: string | null;
  _pinging?: boolean;
  _pingResult?: 'ok' | 'error' | null;
}

interface Controlador {
  id: number;
  nombre: string;
  ip: string;
  puerto: number;
  activo: boolean;
  ultimo_contacto: string | null;
  _pinging?: boolean;
  _pingResult?: 'ok' | 'error' | null;
}

@Component({
  selector: 'app-hardware',
  standalone: true,
  imports: [NgIf, NgFor, NgClass],
  templateUrl: './hardware.component.html',
  styleUrl: './hardware.component.css',
})
export class HardwareComponent implements OnInit, OnDestroy {

  loading  = false;
  error    = '';
  ultimaActualizacion = '';

  terminales:   Terminal[]    = [];
  controladores: Controlador[] = [];

  private refreshId: any = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargar();
    // Refresca el estado cada 30s
    this.refreshId = setInterval(() => this.cargar(false), 30_000);
  }

  ngOnDestroy(): void {
    if (this.refreshId) clearInterval(this.refreshId);
  }

  // ── Carga ──────────────────────────────────────────────────────

  cargar(mostrarLoading = true): void {
    if (mostrarLoading) this.loading = true;
    this.error = '';

    forkJoin({
      terminales:    this.api.getTerminales(),
      controladores: this.api.getControladores(),
    }).subscribe({
      next: ({ terminales, controladores }) => {
        this.terminales    = terminales   as Terminal[];
        this.controladores = controladores as Controlador[];
        this.loading = false;
        const now = new Date();
        this.ultimaActualizacion =
          `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error   = err?.error?.detail ?? 'Error al cargar dispositivos.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  // ── Ping ───────────────────────────────────────────────────────

  ping(dispositivo: Terminal | Controlador): void {
    if (dispositivo._pinging) return;
    dispositivo._pinging    = true;
    dispositivo._pingResult = null;

    this.api.pingHardware(dispositivo.id).subscribe({
      next: () => {
        dispositivo._pinging    = false;
        dispositivo._pingResult = 'ok';
        dispositivo.activo      = true;
        this.cdr.detectChanges();
        setTimeout(() => { dispositivo._pingResult = null; this.cdr.detectChanges(); }, 4000);
      },
      error: () => {
        dispositivo._pinging    = false;
        dispositivo._pingResult = 'error';
        this.cdr.detectChanges();
        setTimeout(() => { dispositivo._pingResult = null; this.cdr.detectChanges(); }, 4000);
      },
    });
  }

  // ── Helpers ────────────────────────────────────────────────────

  fmtContacto(ts: string | null): string {
    if (!ts) return 'Nunca';
    const d = new Date(ts);
    const diffMs = Date.now() - d.getTime();
    const diffMin = Math.floor(diffMs / 60_000);
    if (diffMin < 1)  return 'Ahora';
    if (diffMin < 60) return `hace ${diffMin}m`;
    const h = Math.floor(diffMin / 60);
    if (h < 24) return `hace ${h}h`;
    return d.toLocaleDateString('es', { day: '2-digit', month: '2-digit' });
  }

  get statsTerminales() {
    const total   = this.terminales.length;
    const online  = this.terminales.filter(t => t.activo).length;
    const offline = total - online;
    return { total, online, offline };
  }

  get statsControladores() {
    const total   = this.controladores.length;
    const online  = this.controladores.filter(c => c.activo).length;
    const offline = total - online;
    return { total, online, offline };
  }
}
