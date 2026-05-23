# Decisiones tecnicas

## Plataforma de automatizacion

La solucion prioriza n8n como orquestador porque permite versionar flujos en JSON,
autoalojar la automatizacion, auditar ejecuciones y separar credenciales por entorno.
Make es util para prototipos rapidos, pero para este caso n8n ofrece mejor control
operativo y trazabilidad tecnica.

## Arquitectura

- n8n recibe o simula el disparador del registro mediante webhook.
- La aplicacion Python expone la API del flujo educativo.
- El generador de contenido usa un modelo de lenguaje local mediante Ollama cuando
  esta configurado. En modo demo usa un generador deterministico para permitir pruebas
  sin credenciales.
- El resultado se notifica por los canales configurados: email, Slack y/o WhatsApp.
  En local se crean evidencias en `data/outbox`; en produccion se activan SMTP,
  Slack Incoming Webhook, un webhook WhatsApp/Kapso o WhatsApp Cloud API.
- SQLite persiste registros, puntajes, estado y rutas de constancias.
- Los aprobados reciben una constancia PDF generada con ReportLab.

## Seguridad

- Ninguna credencial queda en el codigo fuente.
- Las variables sensibles viven en `.env`, excluido por `.gitignore`.
- El webhook no guarda secretos en logs.
- Los canales de comunicacion se activan por entorno sin cambiar el codigo.
- La persistencia local se concentra en `data/`, carpeta excluida para artefactos
  operativos.

## Calidad

- Type hints en la logica principal.
- Manejo de errores basico en integraciones externas.
- Tests unitarios para evaluacion del quiz, generacion de contenido y constancias.
- Flujo verificable por API, interfaz web y script de demo.
