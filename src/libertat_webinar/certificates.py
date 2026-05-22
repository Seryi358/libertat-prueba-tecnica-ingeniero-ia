from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


CERTIFICATE_DIR = Path("data/constancias")


def generate_certificate(
    registration_id: str,
    name: str,
    topic: str,
    attendance_date: str,
    score: float,
) -> Path:
    """Crea una constancia PDF simple para usuarios aprobados."""
    CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)
    output = CERTIFICATE_DIR / f"constancia_{registration_id}.pdf"

    page_size = landscape(letter)
    pdf = canvas.Canvas(str(output), pagesize=page_size)
    width, height = page_size

    pdf.setFillColor(colors.HexColor("#0F2D3A"))
    pdf.rect(0, 0, width, height, fill=True, stroke=False)
    pdf.setStrokeColor(colors.HexColor("#54C6A2"))
    pdf.setLineWidth(3)
    pdf.rect(0.55 * inch, 0.55 * inch, width - 1.1 * inch, height - 1.1 * inch)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 1.45 * inch, "Constancia de participacion")

    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 2.05 * inch, "Libertat certifica que")

    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 2.8 * inch, name)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 3.45 * inch, "completo satisfactoriamente el webinar")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 4.0 * inch, topic)

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(
        width / 2,
        height - 4.7 * inch,
        f"Fecha de asistencia: {attendance_date}  |  Puntaje: {score:.0f}%",
    )
    pdf.drawCentredString(width / 2, 1.35 * inch, f"Emitida el {date.today().isoformat()}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, 1.0 * inch, "Educacion financiera para decisiones conscientes")

    pdf.save()
    return output
