from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class ResultadoAcceso(str, Enum):
    EXITOSO = "exitoso"
    DENEGADO_BIOMETRIA = "denegado_biometria"
    DENEGADO_USUARIO_INACTIVO = "denegado_usuario_inactivo"
    DENEGADO_SIN_CASILLERO = "denegado_sin_casillero"
    DENEGADO_FUERA_HORARIO = "denegado_fuera_horario"
    DENEGADO_DISPOSITIVO_NO_AUTORIZADO = "denegado_dispositivo_no_autorizado"
    ERROR_HARDWARE = "error_hardware"

@dataclass
class AccesoLog:
    id: Optional[int]
    usuario_id: Optional[int]
    casillero_id: Optional[int]
    terminal_id: str
    resultado: ResultadoAcceso
    confianza_biometrica: Optional[float]   # Score 0.0 - 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    detalle: Optional[str] = None

    def fue_exitoso(self) -> bool:
        return self.resultado == ResultadoAcceso.EXITOSO
