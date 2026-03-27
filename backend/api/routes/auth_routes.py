# ══════════════════════════════════════════════════════════════
#  api/routes/auth_routes.py
#  Endpoints de autenticación: login + refresh token
# ══════════════════════════════════════════════════════════════

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import jwt, JWTError

from config.settings import settings
from infrastructure.database.conexion import get_db
from infrastructure.database.administrador_repo import AdministradorRepository

router = APIRouter(tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Schemas ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int          # segundos hasta que expira el access token


# ── Helpers de JWT ───────────────────────────────────────────
def _crear_token(data: dict, expire_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expire_delta
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def crear_access_token(admin_id: int, email: str, nombre: str, rol: str = "admin") -> str:
    return _crear_token(
        {"sub": str(admin_id), "email": email, "nombre": nombre, "rol": rol, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def crear_refresh_token(admin_id: int, email: str) -> str:
    return _crear_token(
        {"sub": str(admin_id), "email": email, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def verificar_token(token: str, tipo: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != tipo:
            raise JWTError("tipo incorrecto")
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


# ── POST /api/auth/login ──────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo  = AdministradorRepository(db)
    admin = await repo.buscar_por_email(body.email)

    if not admin or not pwd_context.verify(body.password, admin.password_hash):
        # Mismo mensaje para email incorrecto y contraseña incorrecta
        # (evita enumeración de usuarios)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not admin.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    await repo.actualizar_ultimo_acceso(admin.id)

    access  = crear_access_token(admin.id, admin.email, admin.nombre, getattr(admin, "rol", "admin"))
    refresh = crear_refresh_token(admin.id, admin.email)

    return TokenResponse(
        access_token  = access,
        refresh_token = refresh,
        expires_in    = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── POST /api/auth/refresh ────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = verificar_token(body.refresh_token, tipo="refresh")

    admin_id = int(payload["sub"])
    repo     = AdministradorRepository(db)
    admin    = await repo.buscar_por_id(admin_id)

    if not admin or not admin.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    # Emitir nuevos tokens (rotación de refresh token)
    access  = crear_access_token(admin.id, admin.email, admin.nombre, getattr(admin, "rol", "viewer"))
    refresh_nuevo = crear_refresh_token(admin.id, admin.email)

    return TokenResponse(
        access_token  = access,
        refresh_token = refresh_nuevo,
        expires_in    = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── POST /api/auth/logout ─────────────────────────────────────
@router.post("/logout", status_code=204)
async def logout():
    # El frontend limpia el token localmente.
    # Este endpoint existe para invalidar tokens en una lista negra
    # (implementación futura con Redis).
    return None
