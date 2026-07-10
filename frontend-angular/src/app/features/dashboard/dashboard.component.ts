import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api/api.service';

declare const Chart: any;

interface StatCard {
  label: string;
  value: string | number;
  sub: string;
  color: string;
  icon: string;
}

interface AccesoLog {
  timestamp: string;
  usuario: string;
  terminal_id: string;
  casillero_numero: string;
  resultado: string;
}

interface PisoOcupacion {
  piso: string | number;
  ocupados: number;
  total: number;
  porcentaje_ocupacion: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('chartAccesosCanvas') chartAccesosCanvas!: ElementRef<HTMLCanvasElement>;
  @ViewChild('chartCasillerosCanvas') chartCasillerosCanvas!: ElementRef<HTMLCanvasElement>;

  loading = true;
  error   = '';

  stats: StatCard[] = [];
  ultimosAccesos: AccesoLog[] = [];
  pisos: PisoOcupacion[] = [];
  leyendaCasilleros: { label: string; color: string; count: number }[] = [];

  private chartAccesos: any    = null;
  private chartCasilleros: any = null;
  private dataLoaded = false;
  private viewReady  = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    if (this.dataLoaded) this.renderCharts();
  }

  ngOnDestroy(): void {
    this.chartAccesos?.destroy();
    this.chartCasilleros?.destroy();
  }

  cargar(): void {
    this.loading = true;
    this.error   = '';

    forkJoin({
      ocupacion: this.api.getReporteOcupacion(),
      accesos:   this.api.getReporteAccesos({ limite: '100' }),
    }).subscribe({
      next: ({ ocupacion, accesos }) => {
        this.buildStats(ocupacion.resumen, accesos.resumen);
        this.pisos          = ocupacion.por_piso ?? [];
        this.ultimosAccesos = (accesos.detalle ?? []).slice(0, 10);
        this.buildLeyenda(ocupacion);
        this.loading    = false;
        this.dataLoaded = true;
        if (this.viewReady) this.renderCharts();
        else setTimeout(() => { if (this.viewReady) this.renderCharts(); }, 100);
      },
      error: (err) => {
        this.error   = err?.error?.detail ?? 'Error al cargar datos del dashboard.';
        this.loading = false;
      },
    });
  }

  // ── Builders ──────────────────────────────────────────────

  private buildStats(ocupacion: any, accesos: any): void {
    this.stats = [
      { label: 'Casilleros Ocupados', value: ocupacion?.ocupados ?? '—', sub: `de ${ocupacion?.total ?? '—'} totales`,           color: 'primary', icon: 'fa-lock'         },
      { label: 'Casilleros Libres',   value: ocupacion?.libres   ?? '—', sub: `${ocupacion?.porcentaje_ocupacion ?? 0}% ocupado`, color: 'success', icon: 'fa-lock-open'    },
      { label: 'Accesos Exitosos',    value: accesos?.exitosos    ?? '—', sub: 'en el período',                                   color: 'info',    icon: 'fa-check-circle' },
      { label: 'Accesos Denegados',   value: accesos?.denegados   ?? '—', sub: `${accesos?.tasa_exito ?? 0}% tasa de éxito`,      color: 'danger',  icon: 'fa-times-circle' },
    ];
  }

  private buildLeyenda(data: any): void {
    const estados = ['libre', 'ocupado', 'bloqueado', 'mantenimiento'];
    const colores = ['#28a745', '#007bff', '#dc3545', '#ffc107'];
    this.leyendaCasilleros = estados.map((e, i) => ({
      label: e,
      color: colores[i],
      count: (data.por_piso ?? []).reduce((sum: number, p: any) => sum + (p[e] ?? 0), 0),
    }));
  }

  // ── Charts ────────────────────────────────────────────────

  private renderCharts(): void {
    setTimeout(() => {
      this.renderChartAccesos();
      this.renderChartCasilleros();
    }, 50);
  }

  private renderChartAccesos(): void {
    if (!this.chartAccesosCanvas) return;
    const detalle = this.ultimosAccesos;
    const horas = Array.from({ length: 24 }, (_, h) => ({
      h,
      ex: detalle.filter(l => l.resultado === 'exitoso' && new Date(l.timestamp).getHours() === h).length,
      de: detalle.filter(l => l.resultado !== 'exitoso' && new Date(l.timestamp).getHours() === h).length,
    }));
    this.chartAccesos?.destroy();
    this.chartAccesos = new Chart(this.chartAccesosCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: horas.map(h => `${String(h.h).padStart(2, '0')}:00`),
        datasets: [
          { label: 'Exitosos',  data: horas.map(h => h.ex), backgroundColor: 'rgba(40,167,69,0.7)',  borderRadius: 3 },
          { label: 'Denegados', data: horas.map(h => h.de), backgroundColor: 'rgba(220,53,69,0.7)',  borderRadius: 3 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true } },
      },
    });
  }

  private renderChartCasilleros(): void {
    if (!this.chartCasillerosCanvas) return;
    this.chartCasilleros?.destroy();
    this.chartCasilleros = new Chart(this.chartCasillerosCanvas.nativeElement, {
      type: 'doughnut',
      data: {
        labels: this.leyendaCasilleros.map(l => l.label),
        datasets: [{
          data: this.leyendaCasilleros.map(l => l.count),
          backgroundColor: this.leyendaCasilleros.map(l => l.color),
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        cutout: '65%',
      },
    });
  }

  // ── Helpers plantilla ─────────────────────────────────────

  resultadoBadge(resultado: string): { text: string; cls: string } {
    return resultado === 'exitoso'
      ? { text: 'Exitoso',  cls: 'badge-success' }
      : { text: 'Denegado', cls: 'badge-danger'  };
  }

  pctColor(pct: number): string {
    return pct > 80 ? 'danger' : pct > 50 ? 'warning' : 'success';
  }

  fmtHora(ts: string): string {
    if (!ts) return '—';
    return new Date(ts).toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}
