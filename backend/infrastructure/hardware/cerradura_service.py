import logging
from domain.entities.casillero import Casillero
from infrastructure.hardware.controlador_mqtt import controlador_mqtt

logger = logging.getLogger(__name__)

TIEMPO_APERTURA_SEGUNDOS = 5  # Tiempo que permanece abierta la cerradura

class CerraduraService:
    """
    Traduce órdenes de negocio a comandos físicos del hardware.
    Sabe cómo hablar con el controlador MQTT para cada acción.
    """

    def abrir(self, casillero: Casillero) -> bool:
        """
        Envía la orden de apertura al controlador físico correspondiente.
        Retorna True si el comando fue enviado exitosamente.
        """
        topic = (
            f"casilleros/{casillero.controlador_id}"
            f"/puerto/{casillero.puerto_controlador}/abrir"
        )
        payload = {
            "accion": "abrir",
            "casillero_numero": casillero.numero,
            "duracion_segundos": TIEMPO_APERTURA_SEGUNDOS,
        }
        enviado = controlador_mqtt.publicar(topic, payload)
        if enviado:
            logger.info(
                f"Orden de apertura enviada: casillero {casillero.numero} "
                f"| controlador {casillero.controlador_id}"
            )
        else:
            logger.error(
                f"Fallo al enviar orden de apertura: casillero {casillero.numero}"
            )
        return enviado

    def bloquear(self, casillero: Casillero) -> bool:
        """Bloquea físicamente el casillero (no responde a ningún comando)."""
        topic = (
            f"casilleros/{casillero.controlador_id}"
            f"/puerto/{casillero.puerto_controlador}/bloquear"
        )
        payload = {"accion": "bloquear", "casillero_numero": casillero.numero}
        return controlador_mqtt.publicar(topic, payload)

    def consultar_estado(self, casillero: Casillero) -> bool:
        """Solicita al controlador el estado actual del casillero."""
        topic = (
            f"casilleros/{casillero.controlador_id}"
            f"/puerto/{casillero.puerto_controlador}/estado"
        )
        payload = {"accion": "consultar", "casillero_numero": casillero.numero}
        return controlador_mqtt.publicar(topic, payload)
