from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .certificates import generate_certificate
from .llm import generate_content
from .notifier import send_result_notification
from .quiz import evaluate_quiz
from .schemas import EvaluationInput, RegistrationInput


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Libertat Webinar Automatizacion",
    version="0.1.0",
    description="Flujo educativo con registro, quiz, notificacion y constancia.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.post("/registros")
def create_registration_from_form(
    nombre: str = Form(...),
    email: str = Form(...),
    tema_webinar: str = Form(...),
    fecha_asistencia: str = Form(...),
    telefono: str | None = Form(None),
) -> RedirectResponse:
    data = RegistrationInput(
        nombre=nombre,
        email=email,
        tema_webinar=tema_webinar,
        fecha_asistencia=fecha_asistencia,
        telefono=telefono or None,
    )
    created = create_registration(data)
    return RedirectResponse(url=f"/quiz/{created['id']}", status_code=303)


@app.post("/api/registros")
def create_registration_api(data: RegistrationInput) -> dict[str, str]:
    return create_registration(data)


def create_registration(data: RegistrationInput) -> dict[str, str]:
    registration_id = uuid4().hex
    content = generate_content(data.tema_webinar)
    db.create_registration(registration_id, data, content)
    return {
        "id": registration_id,
        "estado": "pendiente",
        "quiz_url": f"/quiz/{registration_id}",
    }


@app.get("/quiz/{registration_id}", response_class=HTMLResponse)
def quiz_page(registration_id: str, request: Request) -> HTMLResponse:
    row = db.get_registration(registration_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    content = db.content_from_row(row)
    return templates.TemplateResponse(
        request,
        "quiz.html",
        {"registro": row, "contenido": content},
    )


@app.post("/quiz/{registration_id}")
def submit_quiz_form(
    registration_id: str,
    respuesta_0: int = Form(...),
    respuesta_1: int = Form(...),
    respuesta_2: int = Form(...),
) -> RedirectResponse:
    evaluate_registration(registration_id, EvaluationInput(respuestas=[respuesta_0, respuesta_1, respuesta_2]))
    return RedirectResponse(url=f"/resultados/{registration_id}", status_code=303)


@app.post("/api/registros/{registration_id}/evaluar")
def evaluate_registration_api(registration_id: str, payload: EvaluationInput) -> dict:
    return evaluate_registration(registration_id, payload)


def evaluate_registration(registration_id: str, payload: EvaluationInput) -> dict:
    row = db.get_registration(registration_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    content = db.content_from_row(row)
    result = evaluate_quiz(content.quiz, payload.respuestas)
    status = "aprobado" if result.aprobado else "reprobado"
    certificate_path = None

    if result.aprobado:
        certificate_path = generate_certificate(
            registration_id=registration_id,
            name=row["nombre"],
            topic=row["tema_webinar"],
            attendance_date=row["fecha_asistencia"],
            score=result.puntaje,
        )

    db.update_result(registration_id, status, result.puntaje, certificate_path)
    notification_status = send_result_notification(
        registration_id=registration_id,
        recipient=row["email"],
        name=row["nombre"],
        summary=row["resumen"],
        status=status,
        score=result.puntaje,
        certificate_path=certificate_path,
        phone=row["telefono"] if "telefono" in row.keys() else None,
    )
    return {
        "registro_id": registration_id,
        "estado": status,
        "puntaje": result.puntaje,
        "correctas": result.correctas,
        "total": result.total,
        "constancia": str(certificate_path) if certificate_path else None,
        "notificacion": notification_status,
        "detalle": result.detalle,
    }


@app.get("/resultados/{registration_id}", response_class=HTMLResponse)
def result_page(registration_id: str, request: Request) -> HTMLResponse:
    row = db.get_registration(registration_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return templates.TemplateResponse(request, "result.html", {"registro": row})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"registros": db.list_registrations()},
    )


@app.get("/constancias/{filename}")
def download_certificate(filename: str) -> FileResponse:
    path = Path("data/constancias") / filename
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Constancia no encontrada")
    return FileResponse(path, media_type="application/pdf", filename=filename)
