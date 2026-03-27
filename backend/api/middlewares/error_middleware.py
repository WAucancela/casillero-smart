import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def error_handler(request: Request, call_next):
    """
    Captura cualquier excepción no controlada y devuelve una respuesta
    limpia al cliente sin exponer detalles internos del servidor.
    """
    try:
        return await call_next(request)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": "Datos inválidos", "detalle": str(e)}
        )
    except PermissionError as e:
        return JSONResponse(
            status_code=403,
            content={"error": "Sin permisos", "detalle": str(e)}
        )
    except Exception as e:
        logger.exception(f"Error no controlado en {request.url}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )
