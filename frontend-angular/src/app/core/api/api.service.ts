import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {

  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // ── Auth ──────────────────────────────────────────────────────

  login(email: string, password: string): Observable<any> {
    return this.http.post(`${this.base}/auth/login`, { email, password });
  }

  refresh(refreshToken: string): Observable<any> {
    return this.http.post(`${this.base}/auth/refresh`, { refresh_token: refreshToken });
  }

  // ── Usuarios ──────────────────────────────────────────────────

  getUsuarios(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/usuarios/`);
  }

  createUsuario(body: any): Observable<any> {
    return this.http.post(`${this.base}/usuarios/`, body);
  }

  darBajaUsuario(id: number): Observable<any> {
    return this.http.delete(`${this.base}/usuarios/${id}`);
  }

  eliminarUsuario(id: number): Observable<any> {
    return this.http.delete(`${this.base}/usuarios/${id}/eliminar`);
  }

  registrarBiometria(id: number, imagenBase64: string): Observable<any> {
    return this.http.post(`${this.base}/usuarios/${id}/biometria`, { imagen_base64: imagenBase64 });
  }

  // ── Casilleros ────────────────────────────────────────────────

  getCasilleros(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/casilleros/`);
  }

  getCasillerosDisponibles(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/casilleros/disponibles`);
  }

  createCasillero(body: any): Observable<any> {
    return this.http.post(`${this.base}/casilleros/`, body);
  }

  eliminarCasillero(id: number): Observable<any> {
    return this.http.delete(`${this.base}/casilleros/${id}`);
  }

  cambiarEstadoCasillero(id: number, estado: string): Observable<any> {
    return this.http.post(`${this.base}/casilleros/${id}/estado`, { estado });
  }

  asignarCasillero(uid: number): Observable<any> {
    return this.http.post(`${this.base}/casilleros/asignar/${uid}`, {});
  }

  asignarCasilleroManual(cid: number, uid: number): Observable<any> {
    return this.http.post(`${this.base}/casilleros/${cid}/asignar/${uid}`, {});
  }

  liberarCasillero(uid: number): Observable<any> {
    return this.http.delete(`${this.base}/casilleros/liberar/${uid}`);
  }

  abrirCasillero(id: number): Observable<any> {
    return this.http.post(`${this.base}/casilleros/${id}/abrir`, {});
  }

  // ── Accesos ───────────────────────────────────────────────────

  getHistorialAccesos(uid: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/accesos/historial/${uid}`);
  }

  validarAcceso(body: any): Observable<any> {
    return this.http.post(`${this.base}/accesos/validar`, body);
  }

  // ── Reportes ──────────────────────────────────────────────────

  getReporteAccesos(params: Record<string, string> = {}): Observable<any> {
    return this.http.get(`${this.base}/reportes/accesos`, {
      params: new HttpParams({ fromObject: params }),
    });
  }

  getReporteOcupacion(): Observable<any> {
    return this.http.get(`${this.base}/reportes/ocupacion`);
  }

  // ── Hardware ──────────────────────────────────────────────────

  getTerminales(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/hardware/terminales`);
  }

  getControladores(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/hardware/controladores`);
  }

  pingHardware(id: number): Observable<any> {
    return this.http.post(`${this.base}/hardware/${id}/ping`, {});
  }

  // ── Administradores ───────────────────────────────────────────

  getAdmins(): Observable<any[]> {
    return this.http.get<any[]>(`${this.base}/admin/`);
  }

  createAdmin(body: any): Observable<any> {
    return this.http.post(`${this.base}/admin/`, body);
  }

  cambiarRolAdmin(id: number, rol: string): Observable<any> {
    return this.http.patch(`${this.base}/admin/${id}/rol`, { rol });
  }

  toggleActivoAdmin(id: number): Observable<any> {
    return this.http.patch(`${this.base}/admin/${id}/activo`, {});
  }

  getMe(): Observable<any> {
    return this.http.get(`${this.base}/admin/me`);
  }
}
