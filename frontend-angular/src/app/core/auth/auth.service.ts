import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface TokenPayload {
  sub: string;
  email: string;
  nombre?: string;
  rol: string;
  exp: number;
}

export interface TokenInfo {
  email: string;
  sub: string;
  rol: string;
  exp: number;
  expiresAt: string;
  expiresInSec: number;
  expired: boolean;
}

const KEYS = {
  access:  'cas_access_token',
  refresh: 'cas_refresh_token',
  email:   'cas_admin_email',
  nombre:  'cas_admin_nombre',
};

const REFRESH_MARGIN_SEC  = 60;
const INACTIVITY_MINUTES  = 30;

@Injectable({ providedIn: 'root' })
export class AuthService {

  private _isAuth$ = new BehaviorSubject<boolean>(this.hasTokens());
  readonly isAuth$ = this._isAuth$.asObservable();

  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private inactivityTimer: ReturnType<typeof setTimeout> | null = null;
  private refreshLock = false;

  private readonly inactivityEvents = ['mousemove','keydown','click','scroll','touchstart'];
  private readonly boundReset = () => this.resetInactivityTimer();

  constructor(private http: HttpClient, private router: Router) {
    window.addEventListener('storage', (e) => {
      if (e.key === KEYS.access && !e.newValue) {
        this.clearAndRedirect('logout_other_tab');
      }
    });
  }

  // ── Token storage ───────────────────────────────────────────

  setTokens(access: string, refresh: string): void {
    localStorage.setItem(KEYS.access,  access);
    localStorage.setItem(KEYS.refresh, refresh);
  }

  getAccessToken(): string | null  { return localStorage.getItem(KEYS.access);  }
  getRefreshToken(): string | null { return localStorage.getItem(KEYS.refresh); }

  setProfile(email: string, nombre: string): void {
    localStorage.setItem(KEYS.email,  email);
    localStorage.setItem(KEYS.nombre, nombre || email);
  }

  getEmail():  string { return localStorage.getItem(KEYS.email)  ?? ''; }
  getNombre(): string { return localStorage.getItem(KEYS.nombre) ?? ''; }

  hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  }

  clearTokens(): void {
    Object.values(KEYS).forEach(k => localStorage.removeItem(k));
  }

  // ── JWT decode ──────────────────────────────────────────────

  decodePayload(token: string): TokenPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(decodeURIComponent(
        atob(b64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
      ));
    } catch { return null; }
  }

  expiresAt(token: string): number {
    return (this.decodePayload(token)?.exp ?? 0) * 1000;
  }

  isExpired(token: string): boolean {
    const exp = this.expiresAt(token);
    return !exp || Date.now() >= exp;
  }

  expiresInSec(token: string): number {
    return Math.max(0, Math.floor((this.expiresAt(token) - Date.now()) / 1000));
  }

  // ── Session lifecycle ───────────────────────────────────────

  setSession(data: { access_token: string; refresh_token: string }): void {
    this.setTokens(data.access_token, data.refresh_token);
    const payload = this.decodePayload(data.access_token);
    this.setProfile(payload?.email ?? '', payload?.nombre ?? '');
    this._isAuth$.next(true);
    this.scheduleRefresh();
    this.startInactivityWatcher();
  }

  logout(reason = 'manual'): void {
    if (this.refreshTimer)    clearTimeout(this.refreshTimer);
    this.stopInactivityWatcher();
    this.clearTokens();
    this._isAuth$.next(false);
    const params = reason !== 'manual' ? `?reason=${reason}` : '';
    this.router.navigateByUrl('/login' + params);
  }

  async isAuthenticated(): Promise<boolean> {
    if (!this.hasTokens()) return false;
    const token = await this.getValidToken();
    return !!token;
  }

  getTokenInfo(): TokenInfo | null {
    const token = this.getAccessToken();
    if (!token) return null;
    const p = this.decodePayload(token);
    if (!p) return null;
    return {
      email:        p.email,
      sub:          p.sub,
      rol:          p.rol,
      exp:          p.exp,
      expiresAt:    new Date(this.expiresAt(token)).toLocaleString('es-EC'),
      expiresInSec: this.expiresInSec(token),
      expired:      this.isExpired(token),
    };
  }

  getRol(): string {
    const token = this.getAccessToken();
    return token ? (this.decodePayload(token)?.rol ?? '') : '';
  }

  // ── Token refresh ───────────────────────────────────────────

  async getValidToken(): Promise<string | null> {
    const token = this.getAccessToken();
    if (!token) return null;
    if (this.expiresInSec(token) < REFRESH_MARGIN_SEC) return this.doRefresh();
    return token;
  }

  private async doRefresh(): Promise<string | null> {
    if (this.refreshLock) return this.getAccessToken();
    this.refreshLock = true;

    const refreshToken = this.getRefreshToken();
    if (!refreshToken || this.isExpired(refreshToken)) {
      this.refreshLock = false;
      this.logout('session_expired');
      return null;
    }

    try {
      const data: any = await firstValueFrom(
        this.http.post(`${environment.apiUrl}/auth/refresh`, { refresh_token: refreshToken })
      );
      this.setTokens(data.access_token, data.refresh_token ?? refreshToken);
      this.refreshLock = false;
      this.scheduleRefresh();
      return data.access_token;
    } catch {
      this.refreshLock = false;
      return this.getAccessToken();
    }
  }

  private scheduleRefresh(): void {
    if (this.refreshTimer) clearTimeout(this.refreshTimer);
    const token = this.getAccessToken();
    if (!token) return;
    const delay = Math.max(0, (this.expiresInSec(token) - REFRESH_MARGIN_SEC) * 1000);
    this.refreshTimer = setTimeout(() => this.doRefresh(), delay);
  }

  // ── Inactivity watcher ──────────────────────────────────────

  private startInactivityWatcher(): void {
    this.inactivityEvents.forEach(e => document.addEventListener(e, this.boundReset, { passive: true }));
    this.resetInactivityTimer();
  }

  private stopInactivityWatcher(): void {
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    this.inactivityEvents.forEach(e => document.removeEventListener(e, this.boundReset));
  }

  private resetInactivityTimer(): void {
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    this.inactivityTimer = setTimeout(() => this.logout('inactivity'), INACTIVITY_MINUTES * 60 * 1000);
  }

  private clearAndRedirect(reason: string): void {
    this.clearTokens();
    this._isAuth$.next(false);
    this.router.navigateByUrl(`/login?reason=${reason}`);
  }
}
