import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout.component').then(m => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
      },
      {
        path: 'usuarios',
        loadComponent: () => import('./features/usuarios/usuarios.component').then(m => m.UsuariosComponent),
      },
      {
        path: 'casilleros',
        loadComponent: () => import('./features/casilleros/casilleros.component').then(m => m.CasillerosComponent),
      },
      {
        path: 'monitor',
        loadComponent: () => import('./features/monitor/monitor.component').then(m => m.MonitorComponent),
      },
      {
        path: 'reportes',
        loadComponent: () => import('./features/reportes/reportes.component').then(m => m.ReportesComponent),
      },
      {
        path: 'log',
        loadComponent: () => import('./features/log/log.component').then(m => m.LogComponent),
      },
      {
        path: 'hardware',
        loadComponent: () => import('./features/hardware/hardware.component').then(m => m.HardwareComponent),
      },
      {
        path: 'administradores',
        loadComponent: () => import('./features/administradores/administradores.component').then(m => m.AdministradoresComponent),
      },
      {
        path: 'onboarding',
        loadComponent: () => import('./features/onboarding/onboarding.component').then(m => m.OnboardingComponent),
      },
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
