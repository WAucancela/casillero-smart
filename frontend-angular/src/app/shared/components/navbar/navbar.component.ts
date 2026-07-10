import { Component, OnInit, OnDestroy } from '@angular/core';
import { NgClass, NgIf } from '@angular/common';
import { AuthService, TokenInfo } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [NgClass, NgIf],
  templateUrl: './navbar.component.html',
})
export class NavbarComponent implements OnInit, OnDestroy {

  tokenInfo: TokenInfo | null = null;
  showPopover = false;
  private clockInterval: ReturnType<typeof setInterval> | null = null;

  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    this.refreshInfo();
    this.clockInterval = setInterval(() => this.refreshInfo(), 10_000);
  }

  ngOnDestroy(): void {
    if (this.clockInterval) clearInterval(this.clockInterval);
  }

  get sessionStatusClass(): string {
    if (!this.tokenInfo) return 'text-danger';
    if (this.tokenInfo.expired) return 'text-danger';
    if (this.tokenInfo.expiresInSec < 600) return 'text-warning';
    return 'text-success';
  }

  get rolLabel(): string {
    const labels: Record<string, string> = { superadmin: 'Super Usuario', admin: 'Jefatura', viewer: 'Operador' };
    return labels[this.auth.getRol()] ?? '';
  }

  get rolBadgeClass(): string {
    const rol = this.auth.getRol();
    return rol === 'superadmin' ? 'badge-danger' : rol === 'admin' ? 'badge-warning' : 'badge-secondary';
  }

  togglePopover(): void {
    this.showPopover = !this.showPopover;
  }

  renewSession(): void {
    this.auth.getValidToken().then(() => this.refreshInfo());
  }

  logout(): void {
    this.auth.logout('manual');
  }

  private refreshInfo(): void {
    this.tokenInfo = this.auth.getTokenInfo();
  }
}
