from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class RegistrationInput(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    tema_webinar: str = Field(..., min_length=4, max_length=160)
    fecha_asistencia: date
    telefono: str | None = Field(default=None, max_length=40)


class QuizQuestion(BaseModel):
    pregunta: str
    opciones: list[str] = Field(..., min_length=2, max_length=5)
    respuesta_correcta: int = Field(..., ge=0)


class GeneratedContent(BaseModel):
    resumen: str
    quiz: list[QuizQuestion] = Field(..., min_length=3, max_length=3)


class EvaluationInput(BaseModel):
    respuestas: list[int] = Field(..., min_length=3, max_length=3)


class EvaluationResult(BaseModel):
    correctas: int
    total: int
    puntaje: float
    aprobado: bool
    detalle: list[dict[str, Any]]
