import numpy as np
import base64
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class MotorFacial:
    """
    Interfaz con la librería de reconocimiento facial.
    Abstrae DeepFace para que sea fácil cambiar de motor en el futuro.
    """

    def __init__(self):
        self._modelo_cargado = False
        self._modelo = None

    def _cargar_modelo(self):
        """Carga el modelo de forma lazy (solo cuando se necesita)."""
        if not self._modelo_cargado:
            try:
                from deepface import DeepFace
                self._modelo = DeepFace
                self._modelo_cargado = True
                logger.info("Modelo de reconocimiento facial cargado")
            except ImportError:
                logger.error("DeepFace no está instalado: pip install deepface")
                raise

    def generar_vector_desde_imagen(self, imagen_base64: str) -> Optional[list]:
        """
        Recibe una imagen en base64 y devuelve su vector facial (embedding).
        Devuelve None si no detecta un rostro válido.
        """
        self._cargar_modelo()
        try:
            import tempfile, os
            imagen_bytes = base64.b64decode(imagen_base64)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp.write(imagen_bytes)
                tmp_path = tmp.name

            resultado = self._modelo.represent(
                img_path=tmp_path,
                model_name="Facenet512",
                enforce_detection=True,
            )
            os.unlink(tmp_path)

            if resultado:
                return resultado[0]["embedding"]
            return None

        except Exception as e:
            logger.warning(f"No se pudo generar vector facial: {e}")
            return None

    def calcular_similitud(
        self,
        vector_entrada: list,
        vector_almacenado: list
    ) -> float:
        """
        Calcula la similitud coseno entre dos vectores faciales.
        Retorna un score entre 0.0 (diferente) y 1.0 (idéntico).
        """
        v1 = np.array(vector_entrada)
        v2 = np.array(vector_almacenado)
        similitud = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        return float(similitud)

    def comparar_con_multiples_vectores(
        self,
        vector_entrada: list,
        vectores_candidatos: list[Tuple[int, list]]  # [(usuario_id, vector), ...]
    ) -> Optional[Tuple[int, float]]:
        """
        Compara el vector de entrada contra múltiples vectores almacenados.
        Retorna (usuario_id, score) del mejor match, o None si no supera umbral.
        """
        if not vectores_candidatos:
            return None

        mejor_match = None
        mejor_score = 0.0

        for usuario_id, vector in vectores_candidatos:
            score = self.calcular_similitud(vector_entrada, vector)
            if score > mejor_score:
                mejor_score = score
                mejor_match = usuario_id

        return (mejor_match, mejor_score) if mejor_match else None
