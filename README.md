# Mini-plataforma de automatizacion educativa Libertat

Solucion para automatizar el seguimiento posterior a un webinar de educacion
financiera. El flujo captura un registro, genera resumen y quiz, evalua respuestas,
notifica el resultado por email y emite una constancia PDF para usuarios aprobados.

## Funcionalidades

- Trigger por formulario web o webhook REST.
- Generacion de resumen y quiz de 3 preguntas segun el tema del webinar.
- Evaluacion automatica con aprobacion cuando el puntaje es mayor a 70%.
- Notificacion personalizada por email, Slack o WhatsApp segun variables de entorno.
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
| `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET` | Cliente OAuth para Gmail API |
| `GMAIL_REFRESH_TOKEN` | Token OAuth offline para enviar por Gmail API |
| `GMAIL_FROM` | Remitente autorizado por Gmail API |
| `NOTIFICATION_CHANNELS` | Canales separados por coma: `email`, `slack`, `whatsapp` |
| `SLACK_WEBHOOK_URL` | Incoming Webhook para Slack |
| `EVOLUTION_API_URL` / `EVOLUTION_API_KEY` / `EVOLUTION_INSTANCE` | Credenciales Evolution API |
| `WHATSAPP_WEBHOOK_URL` | Webhook de proveedor WhatsApp, por ejemplo Kapso |
| `WHATSAPP_GRAPH_API_VERSION` | Version de Graph API para WhatsApp Cloud API |
| `WHATSAPP_PHONE_NUMBER_ID` / `WHATSAPP_ACCESS_TOKEN` | Credenciales WhatsApp Cloud API |
| `WHATSAPP_DEFAULT_TO` | Destino WhatsApp de prueba si el registro no trae telefono |

## Notificaciones

El canal minimo requerido por la prueba es uno de estos: email, WhatsApp o Slack.
La aplicacion soporta los tres por configuracion. Por defecto usa email y, si no
hay SMTP configurado, guarda una evidencia `.eml` en `data/outbox/` para que el
flujo sea verificable sin credenciales. En produccion se activa SMTP real con:

```env
NOTIFICATION_CHANNELS=email
SMTP_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=usuario
SMTP_PASSWORD=clave
SMTP_FROM=educacion@libertat.co
```

Tambien puede enviarse por Gmail API. Primero se obtiene la URL de autorizacion:

```bash
GMAIL_CLIENT_ID=... python scripts/gmail_oauth_setup.py url
```

Tambien se puede iniciar un servidor local que espera el callback OAuth:

```bash
GMAIL_CLIENT_ID=... GMAIL_CLIENT_SECRET=... python scripts/gmail_oauth_setup.py listen
```

El redirect URI que debe existir en Google Cloud Console es:

```text
http://127.0.0.1:8765/oauth2callback
```

Si se prefiere intercambiar manualmente el codigo recibido:

```bash
GMAIL_CLIENT_ID=... GMAIL_CLIENT_SECRET=... GMAIL_AUTH_CODE=... python scripts/gmail_oauth_setup.py exchange
```

Con el refresh token resultante:

```env
NOTIFICATION_CHANNELS=email
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
GMAIL_FROM=correo_autorizado@gmail.com
```

Para Slack:

```env
NOTIFICATION_CHANNELS=email,slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Para WhatsApp con webhook de proveedor:

```env
NOTIFICATION_CHANNELS=email,whatsapp
WHATSAPP_WEBHOOK_URL=https://proveedor.example.com/webhook
```

Para WhatsApp con Evolution API:

```env
NOTIFICATION_CHANNELS=email,whatsapp
EVOLUTION_API_URL=https://evolution.example.com
EVOLUTION_API_KEY=apikey
EVOLUTION_INSTANCE=nombre_instancia
```

Para WhatsApp Cloud API:

```env
NOTIFICATION_CHANNELS=email,whatsapp
WHATSAPP_GRAPH_API_VERSION=v23.0
WHATSAPP_PHONE_NUMBER_ID=phone_number_id
WHATSAPP_ACCESS_TOKEN=token
```

## n8n

Importa `n8n/flujo_webinar_libertat.json` en n8n. El flujo expone un webhook,
envia el payload a la API Python y responde con el identificador del registro y la
URL del quiz.

Webhook de produccion:

```text
https://n8n-n8n.zb12wf.easypanel.host/webhook/webinar-libertat
```

Payload esperado:

```json
{
  "nombre": "Sergio Alejandro Castellanos",
  "email": "scastellanos@phinodia.com",
  "telefono": "+573001234567",
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

## Cumplimiento de la prueba

La matriz punto a punto contra el PDF de instrucciones esta en
`docs/cumplimiento_pdf.md`.
