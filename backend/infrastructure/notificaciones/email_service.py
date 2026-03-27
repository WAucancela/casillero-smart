import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Envía notificaciones por correo electrónico.
    Si cambias de proveedor de email, solo modificas este archivo.
    """

    def _crear_conexion(self):
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        return server

    def _enviar(self, destinatario: str, asunto: str, cuerpo_html: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = asunto
            msg["From"] = settings.SMTP_USER
            msg["To"] = destinatario
            msg.attach(MIMEText(cuerpo_html, "html"))

            with self._crear_conexion() as server:
                server.sendmail(settings.SMTP_USER, destinatario, msg.as_string())

            logger.info(f"Email enviado a {destinatario}: {asunto}")
            return True
        except Exception as e:
            logger.error(f"Error al enviar email a {destinatario}: {e}")
            return False

    def notificar_casillero_asignado(
        self,
        email: str,
        nombre: str,
        numero_casillero: str,
        piso: int
    ) -> bool:
        asunto = "Tu casillero ha sido asignado"
        cuerpo = f"""
        <h2>¡Hola {nombre}!</h2>
        <p>Tu casillero ha sido asignado exitosamente:</p>
        <ul>
            <li><strong>Número:</strong> {numero_casillero}</li>
            <li><strong>Piso:</strong> {piso}</li>
        </ul>
        <p>Para acceder, dirígete a la terminal de reconocimiento facial más cercana.</p>
        """
        return self._enviar(email, asunto, cuerpo)

    def notificar_registro_biometria(self, email: str, nombre: str) -> bool:
        asunto = "Registro biométrico completado"
        cuerpo = f"""
        <h2>¡Hola {nombre}!</h2>
        <p>Tu registro de reconocimiento facial fue completado exitosamente.</p>
        <p>Ya puedes acceder a tu casillero usando la terminal facial.</p>
        """
        return self._enviar(email, asunto, cuerpo)

    def notificar_acceso_denegado_repetido(
        self,
        email_admin: str,
        terminal_id: str,
        intentos: int
    ) -> bool:
        asunto = f"⚠️ Alerta: Múltiples intentos fallidos en terminal {terminal_id}"
        cuerpo = f"""
        <h2>Alerta de seguridad</h2>
        <p>Se detectaron <strong>{intentos}</strong> intentos fallidos consecutivos
        en la terminal <strong>{terminal_id}</strong>.</p>
        <p>Por favor verifica la situación.</p>
        """
        return self._enviar(email_admin, asunto, cuerpo)
