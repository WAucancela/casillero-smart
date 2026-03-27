from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.acceso_repo import AccesoRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.database.usuario_repo import UsuarioRepository
from api.middlewares.auth_middleware import jefatura_o_superior

router = APIRouter()

@router.get("/accesos", summary="Reporte de accesos por rango de fechas")
async def reporte_accesos(
    fecha_inicio: Optional[str] = Query(default=None),
    fecha_fin:    Optional[str] = Query(default=None),
    resultado:    Optional[str] = Query(default=None),
    usuario_id:   Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    ahora = datetime.now()
    desde = datetime.fromisoformat(fecha_inicio) if fecha_inicio else ahora - timedelta(days=7)
    hasta = datetime.fromisoformat(fecha_fin)    if fecha_fin    else ahora

    # Extender hasta al final del día
    hasta = hasta.replace(hour=23, minute=59, second=59)

    acceso_repo   = AccesoRepository(db)
    usuario_repo  = UsuarioRepository(db)
    casillero_repo = CasilleroRepository(db)

    logs = await acceso_repo.listar_por_rango_fechas(desde, hasta, usuario_id, resultado)

    # Mapas para enriquecer los datos
    usuarios   = await usuario_repo.listar_todos()
    casilleros = await casillero_repo.listar_todos()
    mapa_usr = {u.id: u.nombre_completo for u in usuarios}
    mapa_cas = {c.id: c.numero          for c in casilleros}

    total     = len(logs)
    exitosos  = sum(1 for log in logs if log.fue_exitoso())
    denegados = total - exitosos

    return {
        "periodo": {"desde": desde.isoformat(), "hasta": hasta.isoformat()},
        "resumen": {
            "total_intentos": total,
            "exitosos":       exitosos,
            "denegados":      denegados,
            "tasa_exito":     round(exitosos / total * 100, 2) if total > 0 else 0,
        },
        "detalle": [
            {
                "id":               log.id,
                "timestamp":        log.timestamp.isoformat(),
                "usuario_id":       log.usuario_id,
                "usuario":          mapa_usr.get(log.usuario_id, "Desconocido"),
                "casillero_id":     log.casillero_id,
                "casillero_numero": mapa_cas.get(log.casillero_id) if log.casillero_id else None,
                "terminal_id":      log.terminal_id,
                "resultado":        log.resultado.value if hasattr(log.resultado, "value") else log.resultado,
                "confianza_biometrica": log.confianza_biometrica,
            }
            for log in logs
        ],
    }

@router.get("/ocupacion", summary="Reporte de ocupación de casilleros")
async def reporte_ocupacion(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(jefatura_o_superior),
):
    repo = CasilleroRepository(db)
    todos = await repo.listar_todos()
    disponibles = await repo.listar_disponibles()

    total = len(todos)
    libres = len(disponibles)
    ocupados = total - libres

    pisos: dict = {}
    for c in todos:
        p = c.piso or 0
        if p not in pisos:
            pisos[p] = {"piso": p, "total": 0, "ocupados": 0, "libres": 0,
                        "libre": 0, "ocupado": 0, "bloqueado": 0, "mantenimiento": 0}
        pisos[p]["total"] += 1
        estado_val = c.estado.value if hasattr(c.estado, "value") else str(c.estado)
        if estado_val in pisos[p]:
            pisos[p][estado_val] += 1
        if c.usuario_asignado_id:
            pisos[p]["ocupados"] += 1
        else:
            pisos[p]["libres"] += 1

    por_piso = []
    for p_data in sorted(pisos.values(), key=lambda x: x["piso"]):
        p_data["porcentaje_ocupacion"] = round(
            p_data["ocupados"] / p_data["total"] * 100, 2
        ) if p_data["total"] > 0 else 0
        por_piso.append(p_data)

    return {
        "resumen": {
            "total": total,
            "ocupados": ocupados,
            "libres": libres,
            "porcentaje_ocupacion": round(ocupados / total * 100, 2) if total > 0 else 0,
        },
        "por_piso": por_piso,
    }
