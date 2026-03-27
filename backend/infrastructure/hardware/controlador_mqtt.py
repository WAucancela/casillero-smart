import paho.mqtt.client as mqtt
import json
import logging
import asyncio
from typing import Callable, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class ControladorMQTT:
    """
    Mantiene la conexión con el broker MQTT y publica/suscribe mensajes.
    Es el único punto de contacto con los controladores físicos de cerraduras.
    """

    TOPIC_ABRIR = "casilleros/{controlador_id}/puerto/{puerto}/abrir"
    TOPIC_ESTADO = "casilleros/{controlador_id}/puerto/{puerto}/estado"
    TOPIC_RESPUESTA = "casilleros/respuesta/#"

    def __init__(self):
        import os
        self._client = mqtt.Client(client_id=f"backend-server-{os.getpid()}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self._callbacks: dict[str, Callable] = {}
        self._conectado = False

    def conectar(self):
        if settings.MQTT_USER:
            self._client.username_pw_set(
                settings.MQTT_USER,
                settings.MQTT_PASSWORD
            )
        self._client.connect(
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            keepalive=60
        )
        self._client.loop_start()
        logger.info(f"Conectando a broker MQTT: {settings.MQTT_BROKER_HOST}")

    def desconectar(self):
        self._client.loop_stop()
        self._client.disconnect()

    def publicar(self, topic: str, payload: dict) -> bool:
        if not self._conectado:
            logger.error("No hay conexión MQTT activa")
            return False
        resultado = self._client.publish(
            topic,
            json.dumps(payload),
            qos=1
        )
        return resultado.rc == mqtt.MQTT_ERR_SUCCESS

    def suscribir(self, topic: str, callback: Callable):
        self._callbacks[topic] = callback
        self._client.subscribe(topic, qos=1)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._conectado = True
            self._client.subscribe(self.TOPIC_RESPUESTA, qos=1)
            logger.info("Conectado al broker MQTT exitosamente")
        else:
            logger.error(f"Error al conectar al broker MQTT, código: {rc}")

    def _on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            for topic_pattern, callback in self._callbacks.items():
                if mqtt.topic_matches_sub(topic_pattern, message.topic):
                    callback(message.topic, payload)
        except Exception as e:
            logger.error(f"Error procesando mensaje MQTT: {e}")

    def _on_disconnect(self, client, userdata, rc):
        self._conectado = False
        if rc != 0:
            logger.warning("Desconexión inesperada del broker MQTT")

# Instancia singleton
controlador_mqtt = ControladorMQTT()
