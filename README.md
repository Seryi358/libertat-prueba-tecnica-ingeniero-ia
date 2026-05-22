# Mini-plataforma de automatizacion educativa Libertat

Solucion para automatizar el seguimiento posterior a un webinar de educacion
financiera. El flujo captura un registro, genera resumen y quiz, evalua respuestas,
notifica el resultado por email y emite una constancia PDF para usuarios aprobados.

## Funcionalidades

- Trigger por formulario web o webhook REST.
- Generacion de resumen y quiz de 3 preguntas segun el tema del webinar.
- Evaluacion automatica con aprobacion cuando el puntaje es mayor a 70%.
- Notificacion personalizada por email. En local se guarda una evidencia `.eml`.
- Constancia PDF con nombre, fecha y puntaje para usuarios aprobados.
- Dashboard con historial de registros y constancias.
- Flujo n8n importable para orquestar el webhook.
- Tests unitarios para la logica principal.

## Requisitos

- Python 3.10 o superior.
- Opcional: Ollama para usar un modelo de lenguaje local.
- Opcional: n8n para ejecutar el flujo de orquestacion.

## Instalacion local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Ejecucion

```bash
uvicorn libertat_webinar.app:app --app-dir src --reload
```

Luego abre:

- Formulario: `http://127.0.0.1:8000/`
- Dashboard: `http://127.0.0.1:8000/dashboard`
- Salud del servicio: `http://127.0.0.1:8000/health`

## Demo por API

```bash
python scripts/demo_run.py
```

El script crea un registro, evalua el quiz con respuestas aprobadas, genera la
constancia PDF y deja una notificacion local en `data/outbox/`.

## Pruebas

```bash
pytest
```

## Variables de entorno

Todas las credenciales se configuran por entorno. Ninguna clave debe quedar en el
codigo fuente.

| Variable | Uso |
| --- | --- |
| `DATABASE_PATH` | Ruta del archivo SQLite |
| `OLLAMA_ENABLED` | Activa generacion con Ollama si vale `true` |
| `OLLAMA_URL` | URL local de Ollama |
| `OLLAMA_MODEL` | Modelo local a usar |
| `SMTP_ENABLED` | Activa envio SMTP real si vale `true` |
| `SMTP_HOST` / `SMTP_PORT` | Servidor SMTP |
| `SMTP_USER` / `SMTP_PASSWORD` | Credenciales SMTP |
| `SMTP_FROM` | Remitente |

## n8n

Importa `n8n/flujo_webinar_libertat.json` en n8n. El flujo expone un webhook,
envia el payload a la API Python y responde con el identificador del registro y la
URL del quiz.

Payload esperado:

```json
{
  "nombre": "Sergio Alejandro Castellanos",
  "email": "scastellanos@phinodia.com",
  "tema_webinar": "Manejo responsable del endeudamiento",
  "fecha_asistencia": "2026-05-22"
}
```

## Despliegue en Easypanel

La guia de despliegue esta en `docs/despliegue_easypanel.md`. La configuracion clave
es crear un servicio App desde GitHub, usar el Dockerfile del repositorio, publicar
el proxy port `8000` y montar `/app/data` como volumen persistente.

## Exportacion HubSpot

La seccion Python/API tambien queda cubierta con `scripts/export_hubspot_contacts.py`.
Uso:

```bash
export HUBSPOT_TOKEN="token_privado"
python scripts/export_hubspot_contacts.py --output contactos.csv
```

El script consulta contactos creados en los ultimos 30 dias, pagina resultados y
maneja errores HTTP relevantes.

## Estructura

```text
src/libertat_webinar/   Aplicacion principal
tests/                  Pruebas unitarias
scripts/                Demos y utilidades
n8n/                    Flujo importable
docs/                   Decisiones, respuestas y evidencias
```

## Evidencias

Las capturas de funcionamiento se encuentran en `docs/evidencias/`:

- `01_formulario.png`
- `02_quiz.png`
- `03_resultado.png`
- `04_dashboard.png`

La seccion escrita esta respondida en `docs/PruebaTecnica_IngenieroIA_Libertat_respondida.pdf`.

## Decisiones tecnicas

Ver `docs/decisiones_tecnicas.md`.
