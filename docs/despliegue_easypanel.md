# Despliegue en Easypanel

## Recomendacion

Si el VPS ya esta activo, conviene desplegar la aplicacion en Easypanel. La prueba
otorga puntos adicionales por despliegue cloud y Easypanel puede construir la imagen
directamente desde el repositorio porque el proyecto incluye `Dockerfile`.

## Servicio de la aplicacion

Crear un servicio tipo **App** con estos valores:

- Source: GitHub repository.
- Repository: `https://github.com/Seryi358/libertat-prueba-tecnica-ingeniero-ia`
- Branch: `main`
- Build: Dockerfile del repositorio.
- Proxy port: `8000`
- Healthcheck: `/health`
- URL desplegada: `https://n8n-libertat-webinar.zb12wf.easypanel.host`

Variables de entorno recomendadas:

```env
APP_ENV=production
APP_BASE_URL=https://n8n-libertat-webinar.zb12wf.easypanel.host
DATABASE_PATH=data/libertat_webinar.sqlite3
OLLAMA_ENABLED=false
SMTP_ENABLED=false
SMTP_FROM=educacion@libertat.local
```

Mount persistente recomendado:

- Tipo: Volume
- Mount path: `/app/data`

Esto conserva SQLite, constancias PDF y outbox local entre reinicios.

## Servicio n8n

Crear n8n desde el template oficial de Easypanel. Despues importar el archivo:

```text
n8n/flujo_webinar_libertat.json
```

El nodo HTTP Request del flujo apunta a la URL publica de la app:

```text
https://n8n-libertat-webinar.zb12wf.easypanel.host/api/registros
```

Activar el workflow y probar el webhook con este payload:

```text
https://n8n-n8n.zb12wf.easypanel.host/webhook/webinar-libertat
```

```json
{
  "nombre": "Sergio Alejandro Castellanos",
  "email": "scastellanos@phinodia.com",
  "tema_webinar": "Manejo responsable del endeudamiento",
  "fecha_asistencia": "2026-05-22"
}
```

La respuesta esperada contiene `id`, `estado` y `quiz_url`.

## Verificacion post-despliegue

1. Abrir `https://n8n-libertat-webinar.zb12wf.easypanel.host/health`; debe responder `{"status":"ok"}`.
2. Abrir `https://n8n-libertat-webinar.zb12wf.easypanel.host/` y crear un registro.
3. Responder el quiz con las opciones 1, 2 y 3 respectivamente.
4. Confirmar resultado aprobado y descarga de constancia.
5. Abrir `https://n8n-libertat-webinar.zb12wf.easypanel.host/dashboard` y revisar el historial.
6. Probar el webhook n8n y verificar que cree un registro nuevo.
