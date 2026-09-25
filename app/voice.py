from pathlib import Path
import os

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from .usage import estimate_tts_usage

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENAI_BASE_URL = "https://api.openai.com/v1"


class VoiceConfigurationError(RuntimeError):
    pass


class VoiceServiceError(RuntimeError):
    pass


def _api_key() -> str:
    value = os.getenv("OPENAI_API_KEY", "").strip()
    if not value:
        raise VoiceConfigurationError(
            "Falta OPENAI_API_KEY. La voz utiliza la misma clave configurada para el simulador."
        )
    return value


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    content_type: str | None,
) -> str:
    if not audio_bytes:
        raise VoiceServiceError("La grabación está vacía.")

    model = (
        os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-transcribe").strip()
        or "gpt-transcribe"
    )

    prompt = (
        "Entrevista universitaria de levantamiento de información. "
        "Una estudiante conversa en español de Chile con Carolina, encargada de Bodega de RetailNova. "
        "El tema incluye recepción de mercadería, inventario, stock, despacho, devoluciones, "
        "registros, planillas Excel y sistemas de información. "
        "Transcribe fielmente lo que dice la estudiante y usa alfabeto latino."
    )

    keywords = [
        "RetailNova",
        "Bodega",
        "inventario",
        "stock",
        "mercadería",
        "recepción",
        "despacho",
        "devoluciones",
        "Excel",
        "sistema",
    ]

    try:
        client = OpenAI(api_key=_api_key())

        file_value = (
            filename or "pregunta.webm",
            audio_bytes,
            content_type or "audio/webm",
        )

        if model == "gpt-transcribe":
            transcription = client.audio.transcriptions.create(
                model=model,
                file=file_value,
                prompt=prompt,
                extra_body={
                    "keywords": keywords,
                    "languages": ["es"],
                },
            )
        else:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=file_value,
                prompt=prompt,
                language="es",
            )
    except Exception as exc:
        raise VoiceServiceError(
            "No fue posible transcribir el audio. Revisa el modelo configurado y vuelve a intentarlo."
        ) from exc

    text = (getattr(transcription, "text", "") or "").strip()
    if not text:
        raise VoiceServiceError(
            "No se pudo reconocer una pregunta en la grabación."
        )

    return {"text": text, "model": model}


def synthesize_speech(text: str) -> dict:
    value = text.strip()
    if not value:
        raise VoiceServiceError("No hay texto para convertir a voz.")

    model = (
        os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()
        or "gpt-4o-mini-tts"
    )
    voice = os.getenv("OPENAI_TTS_VOICE", "marin").strip() or "marin"

    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "voice": voice,
        "input": value[:4096],
        "instructions": (
            "Habla en español latinoamericano natural. "
            "Interpreta a una mujer adulta profesional que trabaja en una empresa. "
            "Usa un tono conversacional, cercano y realista, sin sonar como narradora ni profesora."
        ),
        "response_format": "mp3",
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{OPENAI_BASE_URL}/audio/speech",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise VoiceServiceError(
            "No fue posible generar la voz de Carolina. Revisa el modelo o la voz configurada."
        ) from exc
    except httpx.HTTPError as exc:
        raise VoiceServiceError(
            "No fue posible conectar con el servicio de voz."
        ) from exc

    if not response.content:
        raise VoiceServiceError("El servicio de voz no devolvió audio.")

    return {
        "audio": response.content,
        "usage": estimate_tts_usage(value, model),
    }
