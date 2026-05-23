# Matriz de cumplimiento de la prueba

Este documento contrasta la entrega contra el PDF original de instrucciones.

## Parte 1 - seccion teorico-practica

La seccion escrita esta respondida en:

```text
docs/PruebaTecnica_IngenieroIA_Libertat_respondida.pdf
docs/respuestas_teoricas.md
```

Cobertura:

- Modulo 1.1: diseno de automatizacion con n8n, Notion, Kapso WhatsApp,
  Google Calendar, manejo de errores y seguridad.
- Modulo 1.2: problemas del pseudoflujo y propuesta de mejora.
- Modulo 2.1: script Python para HubSpot entregado en
  `scripts/export_hubspot_contacts.py`.
- Modulo 2.2: analisis de errores del codigo y version corregida conceptual.
- Modulo 3.1: arquitectura de agente con tool-calling, herramientas, prompt e
  handoff humano.
- Modulo 3.2: seleccion de modelo/proveedor, tecnica de prompting y metrica.

## Parte 2 - reto tecnico

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Integrar al menos 3 herramientas | Cubierto | n8n, Python/FastAPI, LLM configurable por API u Ollama, comunicacion por email/Slack/WhatsApp |
| Trigger de entrada por webhook o formulario | Cubierto | `/`, `/api/registros`, workflow `n8n/flujo_webinar_libertat.json` |
| Capturar nombre, email, tema y fecha | Cubierto | `src/libertat_webinar/schemas.py` y formulario web |
| Generar resumen maximo 200 palabras y quiz de 3 preguntas | Cubierto | `src/libertat_webinar/llm.py` |
| Validar quiz y manejar aprobado/reprobado | Cubierto | `src/libertat_webinar/quiz.py` y `src/libertat_webinar/app.py` |
| Notificar resumen y resultado por al menos un canal | Cubierto | `src/libertat_webinar/notifier.py`; soporta email, Slack y WhatsApp |
| Mensaje personalizado con nombre del usuario | Cubierto | `src/libertat_webinar/notifier.py` |
| Generar constancia para aprobados | Cubierto | `src/libertat_webinar/certificates.py` |
| Variables de entorno para credenciales | Cubierto | `.env.example` y `src/libertat_webinar/config.py` |
| Manejo basico de errores en integraciones | Cubierto | LLM con fallback, notificaciones con outbox local, Supabase best-effort, HubSpot con manejo HTTP |
| README con configuracion y ejecucion local | Cubierto | `README.md` |
| Al menos un test unitario de evaluacion | Cubierto | `tests/test_quiz.py` |

## Bonus

| Bonus | Estado | Evidencia |
| --- | --- | --- |
| Guardar resultados en base de datos | Cubierto | SQLite persistente y sincronizacion opcional a Supabase en `src/libertat_webinar/db.py` |
| Dashboard de historial | Cubierto | `/dashboard` y `src/libertat_webinar/templates/dashboard.html` |
| Despliegue cloud | Cubierto | Easypanel: `https://n8n-libertat-webinar.zb12wf.easypanel.host` |

## Evidencias de funcionamiento

Las evidencias visuales estan en `docs/evidencias/`:

- `01_formulario.png`: formulario de registro desplegado.
- `02_quiz.png`: resumen y quiz de 3 preguntas.
- `03_resultado.png`: resultado aprobado y acceso a constancia.
- `04_dashboard.png`: dashboard con historial de registros.
- `demo_funcionamiento.webm`: recorrido grabado del flujo completo.
- `constancia_demo.pdf`: constancia generada para un usuario aprobado.

Ademas, el despliegue quedo validado con envio real por Gmail API y Evolution API
para WhatsApp, y el workflow `Libertat - Webinar educativo` esta activo en n8n.
La base principal es SQLite persistente y se incluye esquema Supabase para
replicacion cloud.

## Verificacion recomendada

```bash
pytest
python -m py_compile $(rg --files -g '*.py')
python -m json.tool n8n/flujo_webinar_libertat.json >/dev/null
python scripts/demo_run.py
```

Para activar Supabase, ejecutar `docs/supabase_schema.sql` en el SQL Editor y
configurar `SUPABASE_SYNC_ENABLED=true`, `SUPABASE_URL` y
`SUPABASE_SERVICE_KEY`.

Para validar notificaciones reales, configurar uno o mas canales:

```env
NOTIFICATION_CHANNELS=email,slack,whatsapp
SMTP_ENABLED=true
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EVOLUTION_API_URL=https://evolution.example.com
EVOLUTION_API_KEY=...
EVOLUTION_INSTANCE=...
WHATSAPP_WEBHOOK_URL=https://proveedor.example.com/webhook
WHATSAPP_GRAPH_API_VERSION=v23.0
```
