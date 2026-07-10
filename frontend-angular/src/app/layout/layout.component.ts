import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../shared/components/sidebar/sidebar.component';
import { NavbarComponent } from '../shared/components/navbar/navbar.component';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent, NavbarComponent],
  template: `
    <div class="wrapper">
      <app-navbar></app-navbar>
      <app-sidebar></app-sidebar>
      <div class="content-wrapper">
        <div class="content">
          <div class="container-fluid pt-3">
            <router-outlet></router-outlet>
          </div>
        </div>
      </div>
      <footer class="main-footer">
        <strong>Casillero Smart</strong> &copy; 2025 Telconet. Todos los derechos reservados.
      </footer>
    </div>
  `,
})
export class LayoutComponent {}
