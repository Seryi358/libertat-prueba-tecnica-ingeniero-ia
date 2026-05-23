from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .config import settings
from .schemas import GeneratedContent, QuizQuestion


def _fallback_content(topic: str) -> GeneratedContent:
    clean_topic = topic.strip()
    resumen = (
        f"En el webinar sobre {clean_topic}, el usuario reviso conceptos clave para tomar "
        "decisiones financieras con mayor criterio: diagnosticar ingresos y gastos, priorizar "
        "obligaciones, construir un presupuesto realista y definir un plan de accion medible. "
        "El enfoque practico consiste en identificar fugas de dinero, separar necesidades de "
        "deseos, crear un fondo de emergencia progresivo y usar indicadores simples como nivel "
        "de endeudamiento, capacidad de ahorro y cumplimiento mensual del presupuesto."
    )
    quiz = [
        QuizQuestion(
            pregunta=f"¿Cual es el primer paso recomendado al trabajar el tema {clean_topic}?",
            opciones=[
                "Medir la situacion actual con datos reales",
                "Tomar un nuevo credito de inmediato",
                "Ignorar gastos pequenos",
            ],
            respuesta_correcta=0,
        ),
        QuizQuestion(
            pregunta="¿Que indicador ayuda a detectar riesgo de sobreendeudamiento?",
            opciones=[
                "Color favorito",
                "Relacion entre deudas e ingresos",
                "Cantidad de contactos telefonicos",
            ],
            respuesta_correcta=1,
        ),
        QuizQuestion(
            pregunta="¿Que habito fortalece la estabilidad financiera?",
            opciones=[
                "Comprar sin presupuesto",
                "Pagar solo cuando haya recordatorios",
                "Separar ahorro antes de gastos variables",
            ],
            respuesta_correcta=2,
        ),
    ]
    return GeneratedContent(resumen=resumen, quiz=quiz)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("La respuesta del modelo no contiene JSON.")
    return json.loads(match.group(0))


def _response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    text_parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                text_parts.append(text)
    return "".join(text_parts)


def _generate_with_model_api(topic: str) -> GeneratedContent:
    prompt = (
        "Genera contenido educativo financiero en espanol para un webinar. "
        "Devuelve exclusivamente JSON valido con esta forma: "
        '{"resumen":"maximo 200 palabras","quiz":[{"pregunta":"...","opciones":["...","...","..."],'
        '"respuesta_correcta":0}]}. '
        "El quiz debe tener exactamente 3 preguntas de seleccion unica, cada una con 3 opciones. "
        "Las respuestas_correctas deben ser indices base cero. "
        f"Tema: {topic}"
    )
    payload = json.dumps(
        {
            "model": settings.model_api_model,
            "input": prompt,
            "text": {"format": {"type": "json_object"}},
            "max_output_tokens": 900,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        settings.model_api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.model_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        raw = json.loads(response.read().decode("utf-8"))

    parsed = _extract_json(_response_text(raw))
    content = GeneratedContent.model_validate(parsed)
    if len(content.resumen.split()) > 200:
        raise ValueError("El resumen excede 200 palabras.")
    return content


def generate_content(topic: str) -> GeneratedContent:
    """Genera resumen y quiz; usa un proveedor configurado y cae a demo local si falla."""
    if (
        settings.model_api_enabled
        and settings.model_api_url
        and settings.model_api_key
        and settings.model_api_model
    ):
        try:
            return _generate_with_model_api(topic)
        except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass

    if not settings.ollama_enabled:
        return _fallback_content(topic)

    prompt = (
        "Genera contenido educativo financiero en espanol para un webinar. "
        "Devuelve exclusivamente JSON valido con esta forma: "
        '{"resumen":"maximo 200 palabras","quiz":[{"pregunta":"...","opciones":["...","...","..."],'
        '"respuesta_correcta":0}]}. '
        "El quiz debe tener exactamente 3 preguntas de seleccion unica, cada una con 3 opciones. "
        f"Tema: {topic}"
    )
    payload = json.dumps(
        {
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
    ).encode("utf-8")

    try:
        request = urllib.request.Request(
            f"{settings.ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = json.loads(response.read().decode("utf-8"))
        parsed = _extract_json(raw.get("response", ""))
        return GeneratedContent.model_validate(parsed)
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return _fallback_content(topic)
