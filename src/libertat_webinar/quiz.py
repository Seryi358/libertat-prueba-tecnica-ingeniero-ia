from __future__ import annotations

from .schemas import EvaluationResult, QuizQuestion


PASSING_SCORE = 70.0


def evaluate_quiz(
    questions: list[QuizQuestion],
    answers: list[int],
    passing_score: float = PASSING_SCORE,
) -> EvaluationResult:
    """Evalua respuestas de seleccion unica y calcula aprobacion."""
    if len(questions) != len(answers):
        raise ValueError("La cantidad de respuestas no coincide con el quiz.")

    detail: list[dict[str, object]] = []
    correct = 0

    for index, (question, selected) in enumerate(zip(questions, answers), start=1):
        is_correct = selected == question.respuesta_correcta
        if is_correct:
            correct += 1
        detail.append(
            {
                "numero": index,
                "pregunta": question.pregunta,
                "respuesta_usuario": selected,
                "respuesta_correcta": question.respuesta_correcta,
                "correcta": is_correct,
            }
        )

    score = round((correct / len(questions)) * 100, 2)
    return EvaluationResult(
        correctas=correct,
        total=len(questions),
        puntaje=score,
        aprobado=score > passing_score,
        detalle=detail,
    )
