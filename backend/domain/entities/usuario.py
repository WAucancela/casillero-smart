from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class EstadoUsuario(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    PENDIENTE_BIOMETRIA = "pendiente_biometria"

@dataclass
class Usuario:
    id: Optional[int]
    nombre: str
    apellido: str
    email: str
    departamento: str
    piso_preferido: Optional[int]
    estado: EstadoUsuario = EstadoUsuario.PENDIENTE_BIOMETRIA
    fecha_creacion: datetime = field(default_factory=datetime.utcnow)
    fecha_actualizacion: Optional[datetime] = None

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def activar(self):
        self.estado = EstadoUsuario.ACTIVO
        self.fecha_actualizacion = datetime.now()

    def desactivar(self):
        self.estado = EstadoUsuario.INACTIVO
        self.fecha_actualizacion = datetime.now()

    def esta_activo(self) -> bool:
        return self.estado == EstadoUsuario.ACTIVO

    def tiene_biometria_pendiente(self) -> bool:
        return self.estado == EstadoUsuario.PENDIENTE_BIOMETRIA
