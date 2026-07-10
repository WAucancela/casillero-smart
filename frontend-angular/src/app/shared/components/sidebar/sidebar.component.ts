import { Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { NgFor, NgIf } from '@angular/common';
import { AuthService } from '../../../core/auth/auth.service';

interface NavItem {
  id: string;
  label: string;
  icon: string;
  route: string;
  roles: string[];
  badge?: { text: string; cls: string };
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard',       label: 'Dashboard',        icon: 'fa-tachometer-alt',  route: '/dashboard',       roles: ['viewer','admin','superadmin'] },
  { id: 'usuarios',        label: 'Usuarios',          icon: 'fa-users',           route: '/usuarios',        roles: ['viewer','admin','superadmin'] },
  { id: 'casilleros',      label: 'Casilleros',        icon: 'fa-boxes',           route: '/casilleros',      roles: ['viewer','admin','superadmin'] },
  { id: 'monitor',         label: 'Monitor',           icon: 'fa-broadcast-tower', route: '/monitor',         roles: ['viewer','admin','superadmin'], badge: { text: 'LIVE', cls: 'badge-success' } },
  { id: 'reportes',        label: 'Reportes',          icon: 'fa-chart-bar',       route: '/reportes',        roles: ['admin','superadmin'] },
  { id: 'log',             label: 'Log Completo',      icon: 'fa-list-alt',        route: '/log',             roles: ['admin','superadmin'] },
  { id: 'hardware',        label: 'Hardware',          icon: 'fa-microchip',       route: '/hardware',        roles: ['superadmin'] },
  { id: 'administradores', label: 'Administradores',   icon: 'fa-user-shield',     route: '/administradores', roles: ['superadmin'] },
];

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, NgFor, NgIf],
  templateUrl: './sidebar.component.html',
})
export class SidebarComponent implements OnInit {

  navItems: NavItem[] = [];
  nombre = '';
  email  = '';
  rol    = '';
  rolLabel = '';

  private readonly rolLabels: Record<string, string> = {
    superadmin: 'Super Usuario',
    admin:      'Jefatura',
    viewer:     'Operador',
  };

  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    this.rol      = this.auth.getRol();
    this.rolLabel = this.rolLabels[this.rol] ?? this.rol;
    this.email    = this.auth.getEmail();
    this.nombre   = this.auth.getNombre() || this.email;
    this.navItems = NAV_ITEMS.filter(item => item.roles.includes(this.rol));
  }

  logout(): void {
    this.auth.logout('manual');
  }
}
