from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "PruebaTecnica_IngenieroIA_Libertat_original.pdf"
OUTPUT = ROOT / "docs" / "PruebaTecnica_IngenieroIA_Libertat_respondida.pdf"


def wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        proposed = " ".join([*current, word])
        if len(proposed) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_chars: int,
    leading: float = 9.5,
    limit: int | None = None,
) -> float:
    lines = wrap(text, max_chars)
    if limit is not None:
        lines = lines[:limit]
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def overlay_page(width: float, height: float, page_number: int) -> BytesIO:
    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=(width, height))
    pdf.setFillColor(colors.HexColor("#0F2D3A"))
    pdf.setFont("Helvetica", 6.4)

    if page_number == 1:
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(282, 344, "Sergio Alejandro Castellanos")
        pdf.drawString(322, 316, "22/05/2026")
        pdf.setFillColor(colors.HexColor("#0F2D3A"))

    if page_number == 2:
        answer = (
            "Uso n8n por autoalojamiento, control de credenciales, auditoria y versionado. "
            "Flujo: Forms/Sheets Trigger -> validar datos -> upsert en Notion -> Kapso WhatsApp -> "
            "Google Calendar -> auditoria. Errores: reintentos con backoff, cola de pendientes y alerta "
            "operativa. Seguridad: minimo dato necesario, cifrado, roles, secretos gestionados y logs sin PII."
        )
        draw_wrapped(pdf, answer, 58, 128, 105, limit=7)

    if page_number == 3:
        pdf.drawString(123, 616, "Excel local no es confiable para concurrencia, disponibilidad ni auditoria.")
        pdf.drawString(123, 591, "SMTP con credenciales planas expone secretos y dificulta rotacion.")
        pdf.drawString(123, 565, "Fecha fija, espera de 60s y email duplicado rompen idempotencia.")
        improvement = (
            "Mejora: CRM/base central como fuente, credenciales seguras, fechas dinamicas, plantillas "
            "transaccionales, reintentos, idempotencia y monitoreo."
        )
        draw_wrapped(pdf, improvement, 58, 538, 106, limit=3)
        q21 = (
            "Entrego script en scripts/export_hubspot_contacts.py: token Bearer desde HUBSPOT_TOKEN, "
            "filtro por createdate de ultimos 30 dias, paginacion con after, limite 100, CSV y manejo "
            "de errores 400/401/429/500."
        )
        draw_wrapped(pdf, q21, 58, 321, 105, limit=6)

    if page_number == 4:
        q22 = (
            "Faltan timeouts, raise_for_status, autenticacion, control de rate limit, validacion de JSON, "
            "streaming por pagina y manejo de errores por contacto. Corregido: cliente con timeout, "
            "paginacion hasta pagina vacia, response.json(), upsert individual controlado y metricas."
        )
        draw_wrapped(pdf, q22, 58, 601, 105, limit=7)
        q31 = (
            "Arquitectura tool-calling con estado controlado. Tools: perfil, cursos, contenido aprobado, "
            "agenda, consentimiento, ticket humano y auditoria. Prompt: tono cercano, educativo, no invasivo, "
            "sin promesas financieras y con confirmacion antes de agendar. Handoff por baja confianza, tema "
            "sensible, solicitud explicita o fallo de herramienta."
        )
        draw_wrapped(pdf, q31, 58, 208, 105, limit=8)

    if page_number == 5:
        pdf.setFont("Helvetica", 6.1)
        rows = [
            ("Clasificador liviano interno", "Etiquetas cerradas + ejemplos", "Accuracy macro / matriz"),
            ("Modelo local o privado", "Rol + limite 150 palabras", "ROUGE-L + revision"),
            ("Modelo supervisado + reglas", "Extraccion estructurada", "Recall riesgo / falsos negativos"),
        ]
        y_values = [596, 540, 487]
        for (model, prompt, metric), y in zip(rows, y_values):
            pdf.drawString(215, y, model)
            pdf.drawString(342, y, prompt)
            pdf.drawString(474, y, metric)

    pdf.save()
    packet.seek(0)
    return packet


def add_answer_appendix(writer: PdfWriter) -> None:
    packet = BytesIO()
    pdf = canvas.Canvas(packet, pagesize=letter)
    width, height = letter

    sections = [
        (
            "1.1 Diseno de automatizacion",
            "Usaria n8n. Permite autoalojamiento, versionado del flujo, observabilidad, reintentos y control "
            "de credenciales. Secuencia: Google Forms/Sheets Trigger, validacion y normalizacion, upsert en "
            "Notion, envio Kapso, consulta de agenda, creacion en Google Calendar y registro de auditoria. "
            "Los errores se manejan con reintentos, cola de pendientes y alertas. En seguridad aplicaria "
            "minimizacion de datos, secretos gestionados, permisos por rol, cifrado en transito y logs sin datos personales.",
        ),
        (
            "1.2 Analisis del flujo",
            "Problemas: Excel local no escala ni audita, SMTP con secretos planos, fecha hardcodeada, espera fija "
            "y email duplicado sin idempotencia. Mejora: fuente central, credenciales seguras, fechas dinamicas, "
            "cola de reintentos, control de duplicados, plantillas transaccionales y monitoreo.",
        ),
        (
            "2.1 API REST HubSpot",
            "El repositorio incluye scripts/export_hubspot_contacts.py. Usa HUBSPOT_TOKEN, filtra contactos creados "
            "en los ultimos 30 dias, pagina con after, exporta CSV y controla 400, 401, 429 y 500.",
        ),
        (
            "2.2 Debugging",
            "La version corregida debe usar timeouts, raise_for_status, response.json(), autenticacion, paginacion "
            "hasta pagina vacia, procesamiento incremental, upsert por contacto, rate limits y trazabilidad de fallos.",
        ),
        (
            "3.1 Agente conversacional",
            "Usaria tool-calling con estado. Tools: perfil, cursos completados, base educativa aprobada, agenda, "
            "consentimiento, ticket humano y auditoria. El prompt define tono cercano, educativo y no invasivo; "
            "prohibe promesas financieras y exige confirmacion antes de agendar. El handoff ocurre por baja confianza, "
            "temas sensibles, peticion del usuario o fallo de herramientas.",
        ),
        (
            "3.2 Evaluacion de modelos",
            "Clasificacion: clasificador liviano interno, etiquetas cerradas y accuracy macro. Resumen: modelo local "
            "o privado, prompt con limite de 150 palabras y revision humana. Riesgo de sobreendeudamiento: modelo "
            "supervisado con reglas, extraccion estructurada y recall alto para reducir falsos negativos.",
        ),
    ]

    def header() -> float:
        pdf.setFillColor(colors.HexColor("#0F2D3A"))
        pdf.rect(0, height - 0.75 * inch, width, 0.75 * inch, fill=True, stroke=False)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(0.75 * inch, height - 0.47 * inch, "Libertat - Respuestas teorico-practicas")
        pdf.setFillColor(colors.HexColor("#17242B"))
        return height - 1.15 * inch

    y = header()
    for title, body in sections:
        if y < 1.45 * inch:
            pdf.showPage()
            y = header()
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(0.75 * inch, y, title)
        y -= 0.22 * inch
        pdf.setFont("Helvetica", 9.2)
        y = draw_wrapped(pdf, body, 0.75 * inch, y, 108, leading=11)
        y -= 0.18 * inch

    pdf.save()
    packet.seek(0)
    appendix = PdfReader(packet)
    for page in appendix.pages:
        writer.add_page(page)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(ORIGINAL))
    writer = PdfWriter()

    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        overlay = PdfReader(overlay_page(width, height, index))
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    add_answer_appendix(writer)
    with OUTPUT.open("wb") as file:
        writer.write(file)
    print(OUTPUT)


if __name__ == "__main__":
    main()
