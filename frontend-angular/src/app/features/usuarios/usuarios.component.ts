import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api/api.service';

interface Usuario {
  id: number;
  nombre: string;
  apellido: string;
  nombre_completo?: string;
  email: string;
  departamento: string;
  piso_preferido?: number;
  casillero_numero?: string;
  estado: 'activo' | 'pendiente_biometria' | 'inactivo';
}

interface CasilleroDisponible {
  id: number;
  numero: string;
  piso: string;
}

const ESTADO_COLOR: Record<string, string> = {
  activo:              'success',
  pendiente_biometria: 'warning',
  inactivo:            'secondary',
};

const ESTADO_ICON: Record<string, string> = {
  activo:              'fa-check-circle',
  pendiente_biometria: 'fa-clock',
  inactivo:            'fa-ban',
};

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule],
  templateUrl: './usuarios.component.html',
})
export class UsuariosComponent implements OnInit {

  loading  = true;
  error    = '';
  usuarios: Usuario[] = [];
  filtrados: Usuario[] = [];

  filtroTexto       = '';
  filtroEstado      = '';
  filtroDepartamento = '';

  modalDetalle   = false;
  modalNuevo     = false;
  modalCasillero = false;

  usuarioSeleccionado: Usuario | null = null;
  casillerosDisponibles: CasilleroDisponible[] = [];
  casilleroSeleccionadoId = '';
  loadingCasilleros = false;

  nuevoForm = { nombre: '', apellido: '', email: '', departamento: '', piso_preferido: '' };
  erroresForm: Record<string, string> = {};
  guardando = false;

  toastMsg  = '';
  toastTipo = '';

  readonly departamentos = ['Tecnología', 'Finanzas', 'RRHH', 'Marketing', 'Operaciones'];
  readonly estadoColor   = ESTADO_COLOR;
  readonly estadoIcon    = ESTADO_ICON;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.loading = true;
    this.error   = '';
    this.api.getUsuarios().subscribe({
      next: (data) => {
        this.usuarios  = data;
        this.aplicarFiltros();
        this.loading   = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error   = err?.error?.detail ?? 'Error al cargar usuarios.';
        this.loading = false;
        this.cdr.detectChanges();
      },
    });
  }

  get statsData() {
    return [
      { label: 'Activos',    value: this.usuarios.filter(u => u.estado === 'activo').length,              color: 'success',   icon: 'fa-check-circle' },
      { label: 'Pendientes', value: this.usuarios.filter(u => u.estado === 'pendiente_biometria').length, color: 'warning',   icon: 'fa-clock'        },
      { label: 'Inactivos',  value: this.usuarios.filter(u => u.estado === 'inactivo').length,            color: 'secondary', icon: 'fa-ban'          },
      { label: 'Total',      value: this.usuarios.length,                                                 color: 'primary',   icon: 'fa-users'        },
    ];
  }

  aplicarFiltros(): void {
    const q  = this.filtroTexto.toLowerCase();
    const st = this.filtroEstado;
    const dp = this.filtroDepartamento;
    this.filtrados = this.usuarios.filter(u => {
      const nombre = `${u.nombre} ${u.apellido}`.toLowerCase();
      if (q  && !nombre.includes(q) && !u.email.toLowerCase().includes(q)) return false;
      if (st && u.estado       !== st) return false;
      if (dp && u.departamento !== dp) return false;
      return true;
    });
  }

  nombreCompleto(u: Usuario): string {
    return u.nombre_completo ?? `${u.nombre} ${u.apellido}`;
  }

  estadoLabel(e: string): string {
    return e.replace(/_/g, ' ');
  }

  // ── Modal detalle ──────────────────────────────────────────

  verDetalle(u: Usuario): void {
    this.usuarioSeleccionado = u;
    this.modalDetalle = true;
  }

  cerrarDetalle(): void {
    this.modalDetalle = false;
    this.usuarioSeleccionado = null;
  }

  darBaja(): void {
    if (!this.usuarioSeleccionado) return;
    if (!confirm('¿Confirma dar de baja a este usuario? Se liberará su casillero.')) return;
    this.api.darBajaUsuario(this.usuarioSeleccionado.id).subscribe({
      next: () => { this.cerrarDetalle(); this.toast('Usuario dado de baja.', 'warning'); this.cargar(); this.cdr.detectChanges(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al dar de baja.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  eliminarUsuario(): void {
    if (!this.usuarioSeleccionado) return;
    if (!confirm('¿Eliminar este usuario permanentemente? Esta acción no se puede deshacer.')) return;
    this.api.eliminarUsuario(this.usuarioSeleccionado.id).subscribe({
      next: () => { this.cerrarDetalle(); this.toast('Usuario eliminado permanentemente.', 'danger'); this.cargar(); this.cdr.detectChanges(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al eliminar.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  // ── Modal nuevo usuario ────────────────────────────────────

  abrirModalNuevo(): void {
    this.nuevoForm   = { nombre: '', apellido: '', email: '', departamento: '', piso_preferido: '' };
    this.erroresForm = {};
    this.modalNuevo  = true;
  }

  guardarNuevoUsuario(): void {
    if (!this.validarForm()) return;
    this.guardando = true;
    const body = {
      nombre:         this.nuevoForm.nombre,
      apellido:       this.nuevoForm.apellido,
      email:          this.nuevoForm.email,
      departamento:   this.nuevoForm.departamento,
      piso_preferido: this.nuevoForm.piso_preferido ? Number(this.nuevoForm.piso_preferido) : null,
    };
    this.api.createUsuario(body).subscribe({
      next: () => {
        this.modalNuevo = false;
        this.toast(`Usuario ${body.nombre} ${body.apellido} creado correctamente.`, 'success');
        this.cargar();
      },
      error: (err) => this.toast(err?.error?.detail ?? 'Error al crear usuario.', 'danger'),
      complete: () => { this.guardando = false; this.cdr.detectChanges(); },
    });
  }

  private validarForm(): boolean {
    const f = this.nuevoForm;
    const e: Record<string, string> = {};
    if (!f.nombre)    e['nombre']    = 'Requerido';
    if (!f.apellido)  e['apellido']  = 'Requerido';
    if (!f.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) e['email'] = 'Email inválido';
    if (!f.departamento) e['departamento'] = 'Requerido';
    this.erroresForm = e;
    return Object.keys(e).length === 0;
  }

  // ── Modal asignar casillero ────────────────────────────────

  abrirModalCasillero(): void {
    this.casilleroSeleccionadoId = '';
    this.casillerosDisponibles   = [];
    this.loadingCasilleros       = true;
    this.modalCasillero          = true;
    this.api.getCasillerosDisponibles().subscribe({
      next: (data) => { this.casillerosDisponibles = data; this.loadingCasilleros = false; this.cdr.detectChanges(); },
      error: ()     => { this.loadingCasilleros = false; this.cdr.detectChanges(); },
    });
  }

  confirmarAsignacion(): void {
    if (!this.casilleroSeleccionadoId || !this.usuarioSeleccionado) return;
    this.api.asignarCasilleroManual(Number(this.casilleroSeleccionadoId), this.usuarioSeleccionado.id).subscribe({
      next: (data: any) => {
        this.modalCasillero = false;
        this.cerrarDetalle();
        this.toast(`Casillero ${data.casillero_numero ?? ''} asignado correctamente.`, 'success');
        this.cargar();
        this.cdr.detectChanges();
      },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al asignar.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  quitarCasillero(): void {
    if (!this.usuarioSeleccionado) return;
    if (!confirm('¿Quitar el casillero asignado a este usuario?')) return;
    this.api.liberarCasillero(this.usuarioSeleccionado.id).subscribe({
      next: () => { this.cerrarDetalle(); this.toast('Casillero liberado.', 'warning'); this.cargar(); this.cdr.detectChanges(); },
      error: (err) => { this.toast(err?.error?.detail ?? 'Error al liberar.', 'danger'); this.cdr.detectChanges(); },
    });
  }

  // ── Toast ──────────────────────────────────────────────────

  toast(msg: string, tipo: string): void {
    this.toastMsg  = msg;
    this.toastTipo = tipo;
    setTimeout(() => { this.toastMsg = ''; this.cdr.detectChanges(); }, 4000);
  }
}
