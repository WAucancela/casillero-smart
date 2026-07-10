import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = async (route, state) => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  const ok = await auth.isAuthenticated();
  if (!ok) {
    router.navigate(['/login'], { queryParams: { next: state.url } });
    return false;
  }
  return true;
};
