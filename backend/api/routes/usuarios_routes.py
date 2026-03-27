from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.notificaciones.email_service import EmailService
from infrastructure.biometria.motor_facial import MotorFacial
from infrastructure.biometria.encriptacion_vectores import EncriptacionVectores
from application.usuarios.crear_usuario import CrearUsuario, CrearUsuarioDTO
from application.usuarios.dar_baja_usuario import DarBajaUsuario
from application.usuarios.eliminar_usuario import EliminarUsuario
from application.usuarios.registrar_biometria import RegistrarBiometria
from api.middlewares.auth_middleware import verificar_token, solo_admin, solo_super, jefatura_o_superior, cualquier_admin

router = APIRouter()

# --- Schemas de entrada/salida ---

class CrearUsuarioRequest(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    departamento: str
    piso_preferido: Optional[int] = None

class RegistrarBiometriaRequest(BaseModel):
    imagen_base64: str  # Imagen del rostro en base64

# --- Endpoints ---

@router.post("/", summary="Crear nuevo usuario")
async def crear_usuario(
    body: CrearUsuarioRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    caso_uso = CrearUsuario(
        usuario_repo=UsuarioRepository(db),
        email_service=EmailService(),
    )
    usuario = await caso_uso.ejecutar(
        CrearUsuarioDTO(**body.model_dump())
    )
    return {"id": usuario.id, "email": usuario.email, "estado": usuario.estado}

@router.post("/{usuario_id}/biometria", summary="Registrar huella facial")
async def registrar_biometria(
    usuario_id: int,
    body: RegistrarBiometriaRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(jefatura_o_superior),
):
    caso_uso = RegistrarBiometria(
        db=db,
        usuario_repo=UsuarioRepository(db),
        motor_facial=MotorFacial(),
        encriptacion=EncriptacionVectores(),
        email_service=EmailService(),
    )
    await caso_uso.ejecutar(usuario_id, body.imagen_base64)
    return {"mensaje": "Biometría registrada exitosamente"}

@router.delete("/{usuario_id}/eliminar", summary="Eliminar usuario permanentemente")
async def eliminar_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    caso_uso = EliminarUsuario(
        usuario_repo=UsuarioRepository(db),
        casillero_repo=CasilleroRepository(db),
    )
    await caso_uso.ejecutar(usuario_id)
    return {"mensaje": f"Usuario {usuario_id} eliminado permanentemente"}

@router.delete("/{usuario_id}", summary="Dar de baja usuario")
async def dar_baja_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    caso_uso = DarBajaUsuario(
        usuario_repo=UsuarioRepository(db),
        casillero_repo=CasilleroRepository(db),
    )
    await caso_uso.ejecutar(usuario_id)
    return {"mensaje": f"Usuario {usuario_id} dado de baja correctamente"}

@router.get("/", summary="Listar todos los usuarios")
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(cualquier_admin),
):
    usuario_repo = UsuarioRepository(db)
    casillero_repo = CasilleroRepository(db)

    usuarios = await usuario_repo.listar_todos()
    casilleros = await casillero_repo.listar_todos()

    # Mapa usuario_id → casillero
    mapa_casilleros = {
        c.usuario_asignado_id: c
        for c in casilleros
        if c.usuario_asignado_id is not None
    }

    return [
        {
            "id": u.id,
            "nombre_completo": u.nombre_completo,
            "nombre": u.nombre,
            "apellido": u.apellido,
            "email": u.email,
            "departamento": u.departamento,
            "piso_preferido": u.piso_preferido,
            "estado": u.estado,
            "casillero_id": mapa_casilleros[u.id].id if u.id in mapa_casilleros else None,
            "casillero_numero": mapa_casilleros[u.id].numero if u.id in mapa_casilleros else None,
        }
        for u in usuarios
    ]
