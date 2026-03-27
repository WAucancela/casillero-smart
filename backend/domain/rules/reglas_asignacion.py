from typing import List, Optional
from domain.entities.casillero import Casillero, EstadoCasillero
from domain.entities.usuario import Usuario

class ReglaAsignacion:
    """
    Contiene las reglas de negocio puras para asignar casilleros.
    No depende de base de datos ni de ningún servicio externo.
    """

    @staticmethod
    def usuario_puede_recibir_casillero(usuario: Usuario) -> tuple[bool, str]:
        if not usuario.esta_activo() and not usuario.tiene_biometria_pendiente():
            return False, "El usuario está inactivo"
        return True, ""

    @staticmethod
    def casillero_esta_disponible(casillero: Casillero) -> bool:
        return casillero.estado == EstadoCasillero.LIBRE

    @staticmethod
    def seleccionar_mejor_casillero(
        casilleros_disponibles: List[Casillero],
        usuario: Usuario
    ) -> Optional[Casillero]:
        """
        Prioriza casilleros por piso preferido del usuario.
        Si no hay en el piso preferido, asigna cualquier disponible.
        """
        if not casilleros_disponibles:
            return None

        if usuario.piso_preferido:
            casilleros_piso = [
                c for c in casilleros_disponibles
                if c.piso == usuario.piso_preferido
            ]
            if casilleros_piso:
                return casilleros_piso[0]

        return casilleros_disponibles[0]
