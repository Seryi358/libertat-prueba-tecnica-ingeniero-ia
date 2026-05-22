# Respuestas teorico-practicas

## Pregunta 1.1

Usaria n8n. La razon principal es que permite autoalojamiento, versionado del flujo,
observabilidad de ejecuciones, reintentos y mejor control de credenciales. El flujo
seria: Google Forms o Google Sheets Trigger, normalizacion de datos, busqueda o
creacion de usuario en Notion, envio de WhatsApp mediante Kapso, consulta de agenda
del asesor, creacion del evento en Google Calendar y registro final de auditoria.

Para errores, separaria errores recuperables y no recuperables. Si falla WhatsApp,
marcaria el envio como pendiente, ejecutaria reintentos con backoff y notificaria a
operaciones despues del tercer fallo. Si falla Notion, no continuaria con Calendar
hasta persistir el lead. En seguridad, usaria credenciales del gestor de n8n,
minimizacion de datos, cifrado en transito, permisos por rol, retencion definida y
trazabilidad sin exponer datos personales en logs.

## Pregunta 1.2

Problema 1: depender de un Excel local rompe disponibilidad, concurrencia y auditoria.
Problema 2: credenciales SMTP en texto plano exponen secretos.
Problema 3: fecha hardcodeada y espera fija de 60 segundos generan comportamiento
fragil. Tambien hay duplicacion de email y no se valida idempotencia.

Mejora propuesta: usar HubSpot como fuente principal, base persistente o CRM para
estado, credenciales seguras, fechas dinamicas por regla de negocio, cola de
reintentos, control de idempotencia y plantillas de email transaccional.

## Pregunta 2.1

La solucion se entrega en el repositorio con un enfoque equivalente: token por
variable de entorno, paginacion, manejo de errores HTTP y exportacion estructurada.
El patron recomendado para HubSpot es llamar `/crm/v3/objects/contacts/search` con
filtro `createdate >= fecha_limite`, paginar con `after`, limitar a 100 resultados
por pagina y escribir CSV con `csv.DictWriter`.

## Pregunta 2.2

Problemas identificados: no hay timeout ni `raise_for_status`, se parsea JSON de
forma manual en vez de `response.json()`, no hay autenticacion ni headers, carga todos
los usuarios en memoria, no maneja rate limits, no valida estructura de respuesta,
envia contactos uno a uno sin control de errores y no registra fallos.

Pseudocodigo corregido:

```python
def sync_users(client, crm_client, page_size: int = 100) -> int:
    synced = 0
    page = 1
    while True:
        response = client.get("/users", params={"page": page, "limit": page_size}, timeout=15)
        response.raise_for_status()
        users = response.json().get("users", [])
        if not users:
            break
        for user in users:
            crm_client.upsert_contact(user)
            synced += 1
        page += 1
    return synced
```

## Pregunta 3.1

Usaria una arquitectura de tool-calling con estado conversacional controlado. El
modelo no debe decidir acciones criticas sin herramientas validadas. Las herramientas
serian: consultar perfil del usuario, consultar cursos completados, buscar contenido
educativo aprobado, crear evento con asesor, registrar consentimiento, abrir ticket
humano y registrar trazabilidad.

El system prompt definiria tono cercano, educativo y no invasivo; prohibiria promesas
financieras, exigiria respuestas breves y pediria confirmacion antes de agendar. El
handoff se activa por baja confianza, tema sensible, solicitud explicita del usuario,
fallo de herramientas o riesgo financiero. El agente resume contexto y transfiere a
un asesor con el historial minimo necesario.

## Pregunta 3.2

| Caso de uso | Modelo/proveedor | Tecnica de prompting | Metrica |
| --- | --- | --- | --- |
| Clasificar intencion del usuario | Clasificador liviano alojado internamente | Instrucciones con etiquetas cerradas y ejemplos representativos | Accuracy macro y matriz de confusion |
| Resumir modulos de cursos | Modelo de lenguaje local o privado | Prompt con rol, limite de 150 palabras, audiencia y criterios de exclusion | ROUGE-L, revision humana y cumplimiento de longitud |
| Detectar riesgo de sobreendeudamiento | Modelo supervisado con reglas de negocio | Extraccion estructurada mas umbrales explicables | Recall de casos de riesgo y tasa de falsos negativos |
