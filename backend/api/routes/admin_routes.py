from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.administrador_repo import AdministradorRepository
from api.middlewares.auth_middleware import solo_super, TODOS_LOS_ROLES

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROL_LABELS = {
    "superadmin": "Super Usuario",
    "admin":      "Jefatura",
    "viewer":     "Operador",
}

class CrearAdminRequest(BaseModel):
    nombre:   str
    apellido: str
    email:    EmailStr
    password: str
    rol:      str = "viewer"

class ActualizarRolRequest(BaseModel):
    rol: str

def _fmt(a) -> dict:
    return {
        "id":           a.id,
        "nombre":       a.nombre,
        "apellido":     a.apellido,
        "email":        a.email,
        "rol":          a.rol,
        "rol_label":    ROL_LABELS.get(a.rol, a.rol),
        "activo":       a.activo,
        "ultimo_acceso": a.ultimo_acceso.isoformat() if a.ultimo_acceso else None,
    }

@router.get("/", summary="Listar administradores")
async def listar(db: AsyncSession = Depends(get_db), admin=Depends(solo_super)):
    repo = AdministradorRepository(db)
    return [_fmt(a) for a in await repo.listar_todos()]

@router.post("/", summary="Crear administrador")
async def crear(body: CrearAdminRequest, db: AsyncSession = Depends(get_db), admin=Depends(solo_super)):
    if body.rol not in TODOS_LOS_ROLES:
        raise HTTPException(400, f"Rol inválido. Valores: {list(TODOS_LOS_ROLES)}")
    repo = AdministradorRepository(db)
    if await repo.buscar_por_email(body.email):
        raise HTTPException(400, "Ya existe un administrador con ese email")
    nuevo = await repo.crear(
        nombre=body.nombre, apellido=body.apellido, email=body.email,
        password_hash=pwd_context.hash(body.password), rol=body.rol,
    )
    await db.commit()
    return _fmt(nuevo)

@router.patch("/{admin_id}/rol", summary="Cambiar rol")
async def cambiar_rol(admin_id: int, body: ActualizarRolRequest,
                      db: AsyncSession = Depends(get_db), admin=Depends(solo_super)):
    if body.rol not in TODOS_LOS_ROLES:
        raise HTTPException(400, "Rol inválido")
    if admin_id == admin["usuario_id"]:
        raise HTTPException(400, "No puedes cambiar tu propio rol")
    repo = AdministradorRepository(db)
    if not await repo.buscar_por_id(admin_id):
        raise HTTPException(404, "Administrador no encontrado")
    await repo.actualizar_rol(admin_id, body.rol)
    await db.commit()
    return {"mensaje": "Rol actualizado"}

@router.patch("/{admin_id}/activo", summary="Activar / desactivar")
async def cambiar_activo(admin_id: int, db: AsyncSession = Depends(get_db), admin=Depends(solo_super)):
    if admin_id == admin["usuario_id"]:
        raise HTTPException(400, "No puedes desactivarte a ti mismo")
    repo = AdministradorRepository(db)
    a = await repo.buscar_por_id(admin_id)
    if not a:
        raise HTTPException(404, "Administrador no encontrado")
    await repo.cambiar_activo(admin_id, not a.activo)
    await db.commit()
    return {"activo": not a.activo}

@router.get("/me", summary="Perfil propio")
async def perfil_propio(db: AsyncSession = Depends(get_db), token=Depends(solo_super)):
    repo = AdministradorRepository(db)
    a = await repo.buscar_por_id(token["usuario_id"])
    return _fmt(a) if a else {}
