from pathlib import Path

from libertat_webinar.certificates import generate_certificate
from libertat_webinar.llm import generate_content


def test_generate_content_returns_summary_and_three_questions() -> None:
    content = generate_content("Presupuesto personal")

    assert len(content.resumen.split()) <= 200
    assert len(content.quiz) == 3
    assert all(len(question.opciones) == 3 for question in content.quiz)


def test_generate_certificate_creates_pdf(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    output = generate_certificate(
        registration_id="abc123",
        name="Sergio Alejandro Castellanos",
        topic="Presupuesto personal",
        attendance_date="2026-05-22",
        score=100,
    )

    assert output.exists()
    assert output.suffix == ".pdf"
    assert Path(output).stat().st_size > 1000
