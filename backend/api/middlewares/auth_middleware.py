from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from config.settings import settings

security = HTTPBearer()

# Jerarquía: superadmin > admin (jefatura) > viewer (operador)
ROL_SUPERADMIN  = "superadmin"
ROL_ADMIN       = "admin"
ROL_VIEWER      = "viewer"
TODOS_LOS_ROLES = (ROL_SUPERADMIN, ROL_ADMIN, ROL_VIEWER)


def verificar_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        usuario_id = payload.get("sub")
        rol = payload.get("rol", ROL_VIEWER)
        if usuario_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"usuario_id": int(usuario_id), "rol": rol, "email": payload.get("email", "")}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def solo_super(token_data: dict = Depends(verificar_token)) -> dict:
    """Solo Super Usuario (superadmin)."""
    if token_data.get("rol") != ROL_SUPERADMIN:
        raise HTTPException(status_code=403, detail="Se requieren permisos de Super Usuario")
    return token_data


def jefatura_o_superior(token_data: dict = Depends(verificar_token)) -> dict:
    """Jefatura o Super Usuario."""
    if token_data.get("rol") not in (ROL_SUPERADMIN, ROL_ADMIN):
        raise HTTPException(status_code=403, detail="Se requieren permisos de Jefatura o superior")
    return token_data


def cualquier_admin(token_data: dict = Depends(verificar_token)) -> dict:
    """Cualquier rol válido (superadmin, admin, viewer)."""
    if token_data.get("rol") not in TODOS_LOS_ROLES:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    return token_data


# Alias de compatibilidad con código existente
solo_admin = jefatura_o_superior
