from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoCasillero(str, Enum):
    LIBRE = "libre"
    OCUPADO = "ocupado"
    BLOQUEADO = "bloqueado"
    MANTENIMIENTO = "mantenimiento"

@dataclass
class Casillero:
    id: Optional[int]
    numero: str
    piso: int
    zona: str
    controlador_id: str         # ID del controlador MQTT al que pertenece
    puerto_controlador: int     # Puerto físico en el controlador (1-8)
    estado: EstadoCasillero = EstadoCasillero.LIBRE
    usuario_asignado_id: Optional[int] = None
    fecha_asignacion: Optional[datetime] = None

    def asignar(self, usuario_id: int):
        self.estado = EstadoCasillero.OCUPADO
        self.usuario_asignado_id = usuario_id
        self.fecha_asignacion = datetime.now()

    def liberar(self):
        self.estado = EstadoCasillero.LIBRE
        self.usuario_asignado_id = None
        self.fecha_asignacion = None

    def bloquear(self):
        self.estado = EstadoCasillero.BLOQUEADO

    def esta_disponible(self) -> bool:
        return self.estado == EstadoCasillero.LIBRE
