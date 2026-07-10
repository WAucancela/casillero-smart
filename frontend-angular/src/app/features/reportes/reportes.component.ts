import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api/api.service';

declare const Chart: any;

interface PisoResumen {
  piso: number;
  total: number;
  ocupados: number;
  libres: number;
  porcentaje_ocupacion: number;
}

interface KPI {
  label: string;
  value: string;
  color: string;
  icon: string;
}

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.css',
})
export class ReportesComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('chartDiarioCanvas')   chartDiarioCanvas!:   ElementRef<HTMLCanvasElement>;
  @ViewChild('chartHoraCanvas')     chartHoraCanvas!:     ElementRef<HTMLCanvasElement>;
  @ViewChild('chartDeptoCanvas')    chartDeptoCanvas!:    ElementRef<HTMLCanvasElement>;

  loading = false;
  error   = '';

  // Filtros
  periodo       = '30';
  fechaDesde    = '';
  fechaHasta    = '';
  mostrarCustom = false;

  // Datos
  kpis:  KPI[]         = [];
  pisos: PisoResumen[] = [];
  datosAccesos: any    = null;

  private chartDiario:  any = null;
  private chartHora:    any = null;
  private chartDepto:   any = null;
  private viewReady         = false;
  private pendingRender: any = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void   { this.cargar(); }

  ngAfterViewInit(): void {
    this.viewReady = true;
    if (this.pendingRender) { this.renderCharts(this.pendingRender); this.pendingRender = null; }
  }

  ngOnDestroy(): void {
    this.chartDiario?.destroy();
    this.chartHora?.destroy();
    this.chartDepto?.destroy();
  }

  // ── Período ────────────────────────────────────────────────

  onPeriodoChange(): void {
    this.mostrarCustom = this.periodo === 'custom';
  }

  private getParams(): Record<string, string> {
    if (this.periodo === 'custom') {
      return { fecha_inicio: this.fechaDesde, fecha_fin: this.fechaHasta };
    }
    const hasta = new Date();
    const desde = new Date(Date.now() - Number(this.periodo) * 24 * 3600_000);
    return {
      fecha_inicio: desde.toISOString().slice(0, 10),
      fecha_fin:    hasta.toISOString().slice(0, 10),
    };
  }

  // ── Carga ──────────────────────────────────────────────────

  cargar(): void {
    this.loading = true;
    this.error   = '';

    forkJoin({
      accesos:   this.api.getReporteAccesos(this.getParams()),
      ocupacion: this.api.getReporteOcupacion(),
    }).subscribe({
      next: ({ accesos, ocupacion }) => {
        this.datosAccesos = accesos;
        this.buildKPIs(accesos.resumen, ocupacion.resumen);
        this.pisos   = ocupacion.por_piso ?? [];
        this.loading = false;
        if (this.viewReady) this.renderCharts(accesos.detalle ?? []);
        else this.pendingRender = accesos.detalle ?? [];
      },
      error: (err) => {
        this.error   = err?.error?.detail ?? 'Error al cargar reportes.';
        this.loading = false;
      },
    });
  }

  // ── KPIs ───────────────────────────────────────────────────

  private buildKPIs(res: any, ocup: any): void {
    this.kpis = [
      { label: 'Total accesos',     value: String(res?.total_intentos ?? '—'),              color: 'primary', icon: 'fa-door-open'    },
      { label: 'Tasa de éxito',     value: `${res?.tasa_exito ?? '—'}%`,                    color: 'success', icon: 'fa-check-circle' },
      { label: '% Ocupación',       value: `${ocup?.porcentaje_ocupacion ?? '—'}%`,         color: 'info',    icon: 'fa-box'          },
      { label: 'Accesos denegados', value: String(res?.denegados ?? '—'),                   color: 'danger',  icon: 'fa-times-circle' },
    ];
  }

  // ── Charts ─────────────────────────────────────────────────

  private renderCharts(detalle: any[]): void {
    setTimeout(() => {
      this.renderChartDiario(detalle);
      this.renderChartHora(detalle);
      this.renderChartDepto(detalle);
    }, 50);
  }

  private renderChartDiario(detalle: any[]): void {
    if (!this.chartDiarioCanvas) return;
    const dias: Record<string, { ex: number; de: number }> = {};
    detalle.forEach(l => {
      const d = l.timestamp.slice(0, 10);
      if (!dias[d]) dias[d] = { ex: 0, de: 0 };
      l.resultado === 'exitoso' ? dias[d].ex++ : dias[d].de++;
    });
    const labels = Object.keys(dias).sort();
    this.chartDiario?.destroy();
    this.chartDiario = new Chart(this.chartDiarioCanvas.nativeElement, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Exitosos',  data: labels.map(d => dias[d].ex), borderColor: '#28a745', backgroundColor: 'rgba(40,167,69,0.1)',  fill: true, tension: 0.3 },
          { label: 'Denegados', data: labels.map(d => dias[d].de), borderColor: '#dc3545', backgroundColor: 'rgba(220,53,69,0.1)',   fill: true, tension: 0.3 },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } },
    });
  }

  private renderChartHora(detalle: any[]): void {
    if (!this.chartHoraCanvas) return;
    const horas = Array.from({ length: 24 }, (_, h) => ({
      h, count: detalle.filter(l => new Date(l.timestamp).getHours() === h).length,
    }));
    this.chartHora?.destroy();
    this.chartHora = new Chart(this.chartHoraCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: horas.map(h => `${String(h.h).padStart(2, '0')}h`),
        datasets: [{ label: 'Accesos', data: horas.map(h => h.count), backgroundColor: 'rgba(0,123,255,0.65)', borderRadius: 3 }],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } },
    });
  }

  private renderChartDepto(detalle: any[]): void {
    if (!this.chartDeptoCanvas) return;
    const deptos: Record<string, number> = {};
    detalle.forEach(l => { if (l.departamento) deptos[l.departamento] = (deptos[l.departamento] || 0) + 1; });
    const labels = Object.keys(deptos);
    const values = labels.map(d => deptos[d]);
    const colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#17a2b8', '#6f42c1'];
    this.chartDepto?.destroy();
    this.chartDepto = new Chart(this.chartDeptoCanvas.nativeElement, {
      type: 'doughnut',
      data: { labels, datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length), borderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } },
    });
  }

  // ── Exportar CSV ───────────────────────────────────────────

  exportCSV(): void {
    if (!this.datosAccesos) return;
    const detalle = this.datosAccesos.detalle ?? [];
    const cols = ['ID', 'Fecha', 'Hora', 'Usuario', 'Departamento', 'Terminal', 'Casillero', 'Resultado'];
    const rows = detalle.map((l: any) => [
      l.id, l.timestamp?.slice(0, 10), l.timestamp?.slice(11, 19),
      l.usuario ?? '', l.departamento ?? '', l.terminal_id ?? '',
      l.casillero_numero ?? '', l.resultado,
    ]);
    const csv = [cols, ...rows].map((r: any[]) => r.join(',')).join('\n');
    const a   = document.createElement('a');
    a.href    = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = `reporte_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  }

  // ── Helpers plantilla ──────────────────────────────────────

  pctColor(pct: number): string {
    return pct > 80 ? 'danger' : pct > 50 ? 'warning' : 'success';
  }
}
