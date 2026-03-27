from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.acceso_repo import AccesoRepository
from infrastructure.hardware.cerradura_service import CerraduraService
from infrastructure.notificaciones.email_service import EmailService
from application.casilleros.asignar_casillero import AsignarCasillero
from application.casilleros.asignar_casillero_manual import AsignarCasilleroManual
from application.casilleros.abrir_casillero_remoto import AbrirCasilleroRemoto
from application.casilleros.liberar_casillero import LiberarCasillero
from domain.entities.casillero import Casillero, EstadoCasillero
from api.middlewares.auth_middleware import solo_admin, solo_super, jefatura_o_superior, cualquier_admin

router = APIRouter()

class CrearCasilleroRequest(BaseModel):
    numero: str
    piso: int
    zona: str
    controlador_id: str
    puerto_controlador: int

class CambiarEstadoRequest(BaseModel):
    estado: str

@router.post("/", summary="Crear nuevo casillero")
async def crear_casillero(
    body: CrearCasilleroRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    repo = CasilleroRepository(db)
    casillero = await repo.crear(Casillero(
        id=None,
        numero=body.numero,
        piso=body.piso,
        zona=body.zona,
        controlador_id=body.controlador_id,
        puerto_controlador=body.puerto_controlador,
    ))
    return {"id": casillero.id, "numero": casillero.numero, "mensaje": "Casillero creado correctamente"}

@router.post("/asignar/{usuario_id}", summary="Asignar casillero a usuario")
async def asignar_casillero(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    caso_uso = AsignarCasillero(
        usuario_repo=UsuarioRepository(db),
        casillero_repo=CasilleroRepository(db),
        email_service=EmailService(),
    )
    casillero = await caso_uso.ejecutar(usuario_id)
    return {
        "casillero_numero": casillero.numero,
        "piso": casillero.piso,
        "zona": casillero.zona,
    }

@router.post("/{casillero_id}/asignar/{usuario_id}", summary="Asignar casillero específico a usuario")
async def asignar_casillero_manual(
    casillero_id: int,
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    caso_uso = AsignarCasilleroManual(
        usuario_repo=UsuarioRepository(db),
        casillero_repo=CasilleroRepository(db),
    )
    casillero = await caso_uso.ejecutar(usuario_id, casillero_id)
    return {"casillero_numero": casillero.numero, "piso": casillero.piso, "zona": casillero.zona}

@router.delete("/liberar/{usuario_id}", summary="Liberar casillero de usuario")
async def liberar_casillero(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    caso_uso = LiberarCasillero(casillero_repo=CasilleroRepository(db))
    numero = await caso_uso.ejecutar(usuario_id)
    return {"mensaje": f"Casillero {numero} liberado correctamente"}

@router.post("/{casillero_id}/abrir", summary="Abrir casillero remotamente")
async def abrir_remotamente(
    casillero_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(cualquier_admin),
):
    caso_uso = AbrirCasilleroRemoto(
        casillero_repo=CasilleroRepository(db),
        cerradura_service=CerraduraService(),
        acceso_repo=AccesoRepository(db),
    )
    enviado = await caso_uso.ejecutar(casillero_id, admin["usuario_id"])
    return {"enviado": enviado, "casillero_id": casillero_id}

@router.delete("/{casillero_id}", summary="Eliminar casillero")
async def eliminar_casillero(
    casillero_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    repo = CasilleroRepository(db)
    casillero = await repo.obtener_por_id(casillero_id)
    if not casillero:
        raise HTTPException(status_code=404, detail="Casillero no encontrado")
    if casillero.usuario_asignado_id:
        raise HTTPException(status_code=400, detail="No se puede eliminar un casillero ocupado. Primero libéralo.")
    eliminado = await repo.eliminar(casillero_id)
    return {"mensaje": f"Casillero {casillero.numero} eliminado correctamente"}

@router.post("/{casillero_id}/estado", summary="Cambiar estado del casillero")
async def cambiar_estado(
    casillero_id: int,
    body: CambiarEstadoRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    try:
        estado = EstadoCasillero(body.estado)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Estado inválido: {body.estado}")
    repo = CasilleroRepository(db)
    casillero = await repo.obtener_por_id(casillero_id)
    if not casillero:
        raise HTTPException(status_code=404, detail="Casillero no encontrado")
    await repo.cambiar_estado(casillero_id, estado)
    return {"mensaje": f"Estado actualizado a {body.estado}"}

@router.get("/", summary="Listar todos los casilleros con estado")
async def listar_casilleros(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(cualquier_admin),
):
    casillero_repo = CasilleroRepository(db)
    usuario_repo   = UsuarioRepository(db)
    casilleros = await casillero_repo.listar_todos()
    usuarios   = await usuario_repo.listar_todos()
    mapa_usr   = {u.id: u.nombre_completo for u in usuarios}
    return [
        {
            "id":                 c.id,
            "numero":             c.numero,
            "piso":               c.piso,
            "zona":               c.zona,
            "estado":             c.estado.value if hasattr(c.estado, "value") else c.estado,
            "usuario_asignado_id":c.usuario_asignado_id,
            "usuario_nombre":     mapa_usr.get(c.usuario_asignado_id) if c.usuario_asignado_id else None,
        }
        for c in casilleros
    ]

@router.get("/disponibles", summary="Listar casilleros disponibles")
async def listar_disponibles(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(cualquier_admin),
):
    repo = CasilleroRepository(db)
    casilleros = await repo.listar_disponibles()
    return [{"id": c.id, "numero": c.numero, "piso": c.piso} for c in casilleros]
