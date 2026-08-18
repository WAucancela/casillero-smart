import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api/api.service';

interface Casillero {
  id: number;
  numero: string;
  piso: number;
  zona: string;
  estado: 'libre' | 'ocupado' | 'bloqueado' | 'mantenimiento';
  usuario_nombre?: string;
  controlador_id?: string;
  puerto_controlador?: number;
}

const ESTADO_BG:     Record<string, string> = { libre: '#f0fff4', ocupado: '#f0f6ff', bloqueado: '#fff5f5', mantenimiento: '#fffdf0' };
const ESTADO_BORDER: Record<string, string> = { libre: '#28a745', ocupado: '#007bff', bloqueado: '#dc3545', mantenimiento: '#ffc107' };
const ESTADO_EMOJI:  Record<string, string> = { libre: '🔓',      ocupado: '🔒',      bloqueado: '⛔',      mantenimiento: '🔧'      };
const ESTADO_COLOR:  Record<string, string> = { libre: 'success', ocupado: 'primary', bloqueado: 'danger',  mantenimiento: 'warning' };

@Component({
  selector: 'app-casilleros',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule],
  templateUrl: './casilleros.component.html',
})
export class CasillerosComponent implements OnInit {

  loading  = true;
  error    = '';
  todos: Casillero[]     = [];
  filtrados: Casillero[] = [];

  filtroPiso   = '';
  filtroEstado = '';

  seleccionado: Casillero | null = null;

  modalNuevo  = false;
  guardandoNuevo = false;
  nuevoForm = { numero: '', piso: '1', zona: '', controlador_id: '', puerto_controlador: '' };
  erroresNuevo: Record<string, string> = {};

  toastMsg  = '';
  toastTipo = '';

  readonly estadoBg     = ESTADO_BG;
  readonly estadoBorder = ESTADO_BORDER;
  readonly estadoEmoji  = ESTADO_EMOJI;
  readonly estadoColor  = ESTADO_COLOR;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void { this.cargar(); }

  // ── Carga ──────────────────────────────────────────────────

  cargar(): void {
    this.loading = true;
    this.error   = '';
    this.api.getCasilleros().subscribe({
      next: (data) => {
        this.todos   = data;
        this.loading = false;
        this.aplicarFiltros();
        if (this.seleccionado) {
          this.seleccionado = this.todos.find(c => c.id === this.seleccionado!.id) ?? null;
        }
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error   = err?.error?.detail ?? 'Error al cargar casilleros.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  // ── Stats ──────────────────────────────────────────────────

  get statsData() {
    return [
      { label: 'Libres',        estado: 'libre',        value: this.todos.filter(c => c.estado === 'libre').length,        color: 'success', icon: 'fa-lock-open'    },
      { label: 'Ocupados',      estado: 'ocupado',      value: this.todos.filter(c => c.estado === 'ocupado').length,      color: 'primary', icon: 'fa-lock'         },
      { label: 'Bloqueados',    estado: 'bloqueado',    value: this.todos.filter(c => c.estado === 'bloqueado').length,    color: 'danger',  icon: 'fa-minus-circle' },
      { label: 'Mantenimiento', estado: 'mantenimiento',value: this.todos.filter(c => c.estado === 'mantenimiento').length,color: 'warning', icon: 'fa-tools'        },
    ];
  }

  filtrarPorEstado(estado: string): void {
    this.filtroEstado = estado;
    this.aplicarFiltros();
  }

  // ── Filtros ────────────────────────────────────────────────

  aplicarFiltros(): void {
    this.filtrados = this.todos.filter(c =>
      (!this.filtroPiso   || c.piso   === Number(this.filtroPiso)) &&
      (!this.filtroEstado || c.estado === this.filtroEstado)
    );
  }

  // ── Selección ──────────────────────────────────────────────

  seleccionar(c: Casillero): void {
    this.seleccionado = c;
  }

  isSelected(c: Casillero): boolean {
    return this.seleccionado?.id === c.id;
  }

  get puedeAbrir(): boolean {
    return !!this.seleccionado &&
      this.seleccionado.estado !== 'bloqueado' &&
      this.seleccionado.estado !== 'mantenimiento';
  }

  get puedeEliminar(): boolean {
    return !!this.seleccionado && this.seleccionado.estado !== 'ocupado';
  }

  // ── Acciones ───────────────────────────────────────────────

  abrirCasillero(): void {
    if (!this.seleccionado) return;
    this.api.abrirCasillero(this.seleccionado.id).subscribe({
      next: () => { this.toast(`Apertura enviada al casillero ${this.seleccionado!.numero}.`, 'success'); this.cdr.detectChanges(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al abrir.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  toggleBloquear(): void {
    if (!this.seleccionado) return;
    const c = this.seleccionado;
    const nuevoEstado = c.estado === 'bloqueado' ? 'libre' : 'bloqueado';
    const accion      = nuevoEstado === 'bloqueado' ? 'bloquear' : 'desbloquear';
    if (!confirm(`¿${accion.charAt(0).toUpperCase() + accion.slice(1)} el casillero ${c.numero}?`)) return;
    this.api.cambiarEstadoCasillero(c.id, nuevoEstado).subscribe({
      next: () => { this.toast(`Casillero ${c.numero} ${nuevoEstado === 'bloqueado' ? 'bloqueado' : 'desbloqueado'}.`, 'info'); this.cargar(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  toggleMantenimiento(): void {
    if (!this.seleccionado) return;
    const c = this.seleccionado;
    const nuevoEstado = c.estado === 'mantenimiento' ? 'libre' : 'mantenimiento';
    const accion      = nuevoEstado === 'mantenimiento' ? 'poner en mantenimiento' : 'quitar de mantenimiento';
    if (!confirm(`¿Desea ${accion} el casillero ${c.numero}?`)) return;
    this.api.cambiarEstadoCasillero(c.id, nuevoEstado).subscribe({
      next: () => { this.toast(`Casillero ${c.numero} actualizado.`, 'info'); this.cargar(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  eliminarCasillero(): void {
    if (!this.seleccionado) return;
    const c = this.seleccionado;
    if (c.estado === 'ocupado') { this.toast('No se puede eliminar un casillero ocupado.', 'warning'); this.cdr.detectChanges(); return; }
    if (!confirm(`¿Eliminar el casillero ${c.numero}? Esta acción no se puede deshacer.`)) return;
    this.api.eliminarCasillero(c.id).subscribe({
      next: () => { this.toast(`Casillero ${c.numero} eliminado.`, 'success'); this.seleccionado = null; this.cargar(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al eliminar.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  // ── Modal nuevo casillero ──────────────────────────────────

  abrirModalNuevo(): void {
    this.nuevoForm   = { numero: '', piso: '1', zona: '', controlador_id: '', puerto_controlador: '' };
    this.erroresNuevo = {};
    this.modalNuevo  = true;
  }

  guardarNuevoCasillero(): void {
    const e: Record<string, string> = {};
    if (!this.nuevoForm.numero)           e['numero']           = 'Requerido';
    if (!this.nuevoForm.zona)             e['zona']             = 'Requerido';
    if (!this.nuevoForm.controlador_id)   e['controlador_id']   = 'Requerido';
    if (!this.nuevoForm.puerto_controlador) e['puerto_controlador'] = 'Requerido';
    this.erroresNuevo = e;
    if (Object.keys(e).length) return;

    this.guardandoNuevo = true;
    const body = {
      numero:             this.nuevoForm.numero,
      piso:               Number(this.nuevoForm.piso),
      zona:               this.nuevoForm.zona,
      controlador_id:     this.nuevoForm.controlador_id,
      puerto_controlador: Number(this.nuevoForm.puerto_controlador),
    };
    this.api.createCasillero(body).subscribe({
      next: (res: any) => {
        this.modalNuevo     = false;
        this.guardandoNuevo = false;
        this.toast(`Casillero ${res.numero} creado correctamente.`, 'success');
        this.cargar();
      },
      error: (err) => {
        this.guardandoNuevo = false;
        this.toast(err?.error?.detail ?? 'Error al crear casillero.', 'danger');
        this.cdr.detectChanges();
      },
    });
  }

  // ── Toast ──────────────────────────────────────────────────

  toast(msg: string, tipo: string): void {
    this.toastMsg  = msg;
    this.toastTipo = tipo;
    setTimeout(() => { this.toastMsg = ''; this.cdr.detectChanges(); }, 4000);
  }

  primerNombre(nombre: string): string {
    return nombre?.split(' ')[0] ?? '';
  }
}
