from libertat_webinar.quiz import evaluate_quiz
from libertat_webinar.schemas import QuizQuestion


def _questions() -> list[QuizQuestion]:
    return [
        QuizQuestion(pregunta="P1", opciones=["A", "B", "C"], respuesta_correcta=0),
        QuizQuestion(pregunta="P2", opciones=["A", "B", "C"], respuesta_correcta=1),
        QuizQuestion(pregunta="P3", opciones=["A", "B", "C"], respuesta_correcta=2),
    ]


def test_evaluate_quiz_approved_when_score_is_above_threshold() -> None:
    result = evaluate_quiz(_questions(), [0, 1, 2])

    assert result.aprobado is True
    assert result.correctas == 3
    assert result.puntaje == 100


def test_evaluate_quiz_rejected_when_score_is_not_above_threshold() -> None:
    result = evaluate_quiz(_questions(), [0, 1, 0])

    assert result.aprobado is False
    assert result.correctas == 2
    assert result.puntaje == 66.67


def test_evaluate_quiz_rejects_mismatched_answer_count() -> None:
    try:
        evaluate_quiz(_questions(), [0, 1])
    except ValueError as exc:
        assert "no coincide" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
