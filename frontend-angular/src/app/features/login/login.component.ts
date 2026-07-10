import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIf } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../core/auth/auth.service';
import { ApiService } from '../../core/api/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, NgIf],
  templateUrl: './login.component.html',
})
export class LoginComponent {

  email    = '';
  password = '';
  loading  = false;
  error    = '';

  constructor(
    private api: ApiService,
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  async onSubmit(): Promise<void> {
    if (!this.email || !this.password) {
      this.error = 'Ingresa tu correo y contraseña.';
      return;
    }
    this.loading = true;
    this.error   = '';
    try {
      const data = await this.api.login(this.email, this.password).toPromise();
      this.auth.setSession(data);
      const next = this.route.snapshot.queryParamMap.get('next') ?? '/dashboard';
      this.router.navigateByUrl(next);
    } catch (err: any) {
      this.error = err?.error?.detail ?? 'Credenciales incorrectas.';
    } finally {
      this.loading = false;
    }
  }
}
