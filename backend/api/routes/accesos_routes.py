from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.database.acceso_repo import AccesoRepository
from infrastructure.biometria.motor_facial import MotorFacial
from infrastructure.biometria.encriptacion_vectores import EncriptacionVectores
from infrastructure.hardware.cerradura_service import CerraduraService
from infrastructure.notificaciones.email_service import EmailService
from application.accesos.validar_acceso import ValidarAcceso, SolicitudAccesoDTO
from api.middlewares.auth_middleware import cualquier_admin

router = APIRouter()

class SolicitudAccesoRequest(BaseModel):
    imagen_base64: str
    terminal_id: str

@router.post("/validar", summary="Validar acceso biométrico desde terminal")
async def validar_acceso(
    body: SolicitudAccesoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint que llama la terminal facial cuando captura un rostro.
    No requiere autenticación JWT porque la terminal es un dispositivo de confianza.
    """
    caso_uso = ValidarAcceso(
        db=db,
        usuario_repo=UsuarioRepository(db),
        casillero_repo=CasilleroRepository(db),
        acceso_repo=AccesoRepository(db),
        motor_facial=MotorFacial(),
        encriptacion=EncriptacionVectores(),
        cerradura_service=CerraduraService(),
        email_service=EmailService(),
    )
    resultado = await caso_uso.ejecutar(
        SolicitudAccesoDTO(
            imagen_base64=body.imagen_base64,
            terminal_id=body.terminal_id,
        )
    )
    return {
        "permitido": resultado.permitido,
        "resultado": resultado.resultado,
        "casillero_numero": resultado.casillero_numero,
        "mensaje": resultado.mensaje,
    }

@router.get("/historial/{usuario_id}", summary="Historial de accesos de un usuario")
async def historial_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(cualquier_admin),
):
    repo = AccesoRepository(db)
    logs = await repo.listar_por_usuario(usuario_id)
    return [
        {
            "id": log.id,
            "resultado": log.resultado,
            "timestamp": log.timestamp.isoformat(),
            "casillero_id": log.casillero_id,
            "confianza": log.confianza_biometrica,
        }
        for log in logs
    ]
