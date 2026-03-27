import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config.settings import settings

logger = logging.getLogger(__name__)

class EncriptacionVectores:
    """
    Encripta y desencripta vectores biométricos usando AES (via Fernet).
    Los vectores NUNCA se guardan en texto plano en la base de datos.
    """

    def __init__(self):
        self._fernet = self._crear_fernet()

    def _crear_fernet(self) -> Fernet:
        clave_raw = settings.BIOMETRIC_ENCRYPTION_KEY.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"casilleros_salt_v1",
            iterations=100_000,
        )
        clave = base64.urlsafe_b64encode(kdf.derive(clave_raw))
        return Fernet(clave)

    def encriptar(self, vector: list) -> str:
        """
        Convierte el vector (lista de floats) a JSON, lo encripta y
        devuelve una cadena base64 segura para guardar en la BD.
        """
        vector_json = json.dumps(vector).encode()
        vector_encriptado = self._fernet.encrypt(vector_json)
        return base64.urlsafe_b64encode(vector_encriptado).decode()

    def desencriptar(self, vector_encriptado: str) -> list:
        """
        Recibe el string encriptado de la BD y devuelve el vector original.
        """
        vector_bytes = base64.urlsafe_b64decode(vector_encriptado.encode())
        vector_json = self._fernet.decrypt(vector_bytes)
        return json.loads(vector_json.decode())
