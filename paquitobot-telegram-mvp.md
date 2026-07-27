# PaquitoBot — MVP en Telegram

## Contexto

PaquitoBot es el asistente virtual de Tecsup, originalmente diseñado como widget flotante embebido en la app de Flutter. Este documento adapta esa idea a un **MVP en Telegram**, para poder ofrecer recordatorios y consultas conversacionales sin las restricciones de WhatsApp (ventana de 24h, plantillas aprobadas, verificación de negocio).

## Por qué Telegram y no WhatsApp

| Criterio | WhatsApp (Cloud API / Twilio) | Telegram Bot API |
|---|---|---|
| Mensajes proactivos (recordatorios) | Requiere plantillas pre-aprobadas por Meta fuera de la ventana de 24h | Sin restricción de horario ni aprobación previa |
| Verificación | Meta Business verificado, número dedicado | Ninguna — se crea con @BotFather en minutos |
| Costo | Tarifa por conversación (Meta) + recargo si usas Twilio | Gratis, sin límite de mensajes |
| Curva de implementación | Alta (webhook público, revisión de plantillas) | Baja — resultados en horas |

**Decisión:** MVP con Telegram Bot API. Se revalúa WhatsApp más adelante si el requisito de canal específico se vuelve innegociable.

## Objetivo del MVP

Un bot de Telegram que:

* Salude y reconozca al alumno vinculado a su `chat_id`.
* Responda preguntas usando la estrategia híbrida: knowledge base local → DeepSeek API si no hay match confiable.
* Envíe recordatorios proactivos (tareas, exámenes, eventos) sin depender de que el alumno escriba primero.
* Sirva como base reutilizable para, más adelante, portar la misma lógica a WhatsApp si se decide.

## Qué se necesita (nada de número de teléfono propio)

1. **Token del bot** — se genera con `/newbot` en @BotFather dentro de Telegram. Es la única credencial de identidad del bot (no un número).
2. **Backend con Python** — usando `python-telegram-bot` (o `aiogram` como alternativa).
3. **Base de datos** — para vincular `chat_id` ↔ alumno, guardar historial y estado de recordatorios ya enviados.
4. **API key de DeepSeek** — almacenada como variable de entorno / secret manager, nunca hardcodeada.
5. **Hosting con proceso persistente** — Railway, Render o un VPS (no requiere HTTPS público si se usa long polling en el MVP).

## Arquitectura propuesta

```
paquitobot-backend/
├── bot/
│   ├── handlers/
│   │   ├── start_handler.py        # /start, /vincular (asocia chat_id ↔ alumno)
│   │   ├── message_handler.py      # mensajes libres del alumno
│   │   └── command_handler.py      # comandos tipo /cursos, /horario
│   ├── services/
│   │   ├── deepseek_service.py     # orquesta KB local → DeepSeek → fallback
│   │   ├── knowledge_base.py       # búsqueda en KB local (cache offline)
│   │   └── reminder_service.py     # lógica de recordatorios
│   ├── jobs/
│   │   └── reminder_job.py         # JobQueue: revisa BD y dispara avisos
│   ├── models/
│   │   ├── student.py
│   │   ├── message.py
│   │   └── reminder.py
│   └── config.py                   # tokens, límites, rate limiting
├── database/
│   └── migrations/
├── tests/
└── main.py
```

## Flujo de interacción

1. Alumno manda `/start` → bot pide vincular su código de alumno (una sola vez).
2. Backend guarda `chat_id` ↔ alumno en la BD.
3. Alumno escribe una consulta libre.
4. Backend busca en KB local (offline, respuesta inmediata si hay match).
5. Si no hay match confiable → llama a DeepSeek con system prompt de Tecsup + contexto del alumno (nombre, carrera, ciclo).
6. Respuesta se cachea en KB local para futuras consultas similares.
7. Un job periódico (`JobQueue`, cada 5 min) revisa tareas/eventos próximos en la BD y manda recordatorios vía `bot.send_message()` a los `chat_id` correspondientes, marcando cada uno como ya enviado.

## Control de costos e IA

* Cachear respuestas frecuentes en KB local para evitar llamadas repetidas a DeepSeek.
* Rate limiting: máximo N consultas/día por alumno (configurable).
* System prompt base: asistente cálido, en español, deriva a canal oficial cuando no hay certeza.

## Pendientes por decidir con el equipo

* Mecanismo exacto de vinculación alumno ↔ `chat_id` (¿código generado desde la app, login con credenciales Tecsup?).
* Persistencia del `JobQueue` (guardar en BD el estado de recordatorios enviados para sobrevivir reinicios).
* Migrar de long polling a webhook cuando se pase de pruebas locales a despliegue estable.
* Evaluar si, a futuro, se porta esta misma lógica de `bot/services/` a un canal WhatsApp (Cloud API) reutilizando la capa de servicios.

## Entregables del MVP

1. Bot funcional en Telegram con `/start`, vinculación de alumno y respuesta conversacional.
2. Integración DeepSeek con fallback a KB local.
3. Sistema de recordatorios vía `JobQueue` + persistencia en BD.
4. Tests unitarios de los servicios principales (`deepseek_service`, `reminder_service`).
