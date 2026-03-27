from datetime import datetime, time
from domain.entities.usuario import Usuario, EstadoUsuario
from domain.entities.casillero import Casillero, EstadoCasillero
from domain.entities.acceso_log import ResultadoAcceso

HORA_INICIO_PERMITIDA = time(6, 0)   # 6:00 AM
HORA_FIN_PERMITIDA = time(22, 0)     # 10:00 PM
UMBRAL_CONFIANZA_BIOMETRICA = 0.75   # 75% mínimo de coincidencia

class ReglaAcceso:
    """
    Contiene las reglas de negocio puras para validar un intento de acceso.
    Devuelve el resultado sin ejecutar ninguna acción.
    """

    @staticmethod
    def validar_confianza_biometrica(score: float) -> tuple[bool, ResultadoAcceso]:
        if score < UMBRAL_CONFIANZA_BIOMETRICA:
            return False, ResultadoAcceso.DENEGADO_BIOMETRIA
        return True, ResultadoAcceso.EXITOSO

    @staticmethod
    def validar_usuario_activo(usuario: Usuario) -> tuple[bool, ResultadoAcceso]:
        # Acepta ACTIVO y PENDIENTE_BIOMETRIA (ZKTeco ya verificó la biometría)
        if usuario.estado == EstadoUsuario.INACTIVO:
            return False, ResultadoAcceso.DENEGADO_USUARIO_INACTIVO
        return True, ResultadoAcceso.EXITOSO

    @staticmethod
    def validar_casillero_asignado(
        casillero: Casillero,
        usuario_id: int
    ) -> tuple[bool, ResultadoAcceso]:
        if casillero.usuario_asignado_id != usuario_id:
            return False, ResultadoAcceso.DENEGADO_SIN_CASILLERO
        return True, ResultadoAcceso.EXITOSO

    @staticmethod
    def validar_horario_permitido(ahora: datetime = None) -> tuple[bool, ResultadoAcceso]:
        if ahora is None:
            ahora = datetime.now()
        hora_actual = ahora.time()
        if not (HORA_INICIO_PERMITIDA <= hora_actual <= HORA_FIN_PERMITIDA):
            return False, ResultadoAcceso.DENEGADO_FUERA_HORARIO
        return True, ResultadoAcceso.EXITOSO

    @classmethod
    def ejecutar_todas_las_validaciones(
        cls,
        score: float,
        usuario: Usuario,
        casillero: Casillero
    ) -> tuple[bool, ResultadoAcceso]:
        """Ejecuta todas las reglas en orden. Detiene al primer fallo."""
        for validacion, *args in [
            (cls.validar_confianza_biometrica, score),
            (cls.validar_usuario_activo, usuario),
            (cls.validar_casillero_asignado, casillero, usuario.id),
            (cls.validar_horario_permitido,),
        ]:
            resultado = validacion(*args)
            if not resultado[0]:
                return resultado
        return True, ResultadoAcceso.EXITOSO
