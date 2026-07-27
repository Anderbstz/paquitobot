# PaquitoBot — Plan MVP (Telegram + OTP + Recordatorios)

## Contexto

PaquitoBot nace como asistente virtual embebido en la app de Flutter de Tecsup. Este plan cubre el **MVP en Telegram**: un bot conversacional con autenticación real de alumnos vía OTP, recordatorios proactivos e integración con DeepSeek, listo para producción básica en Render.

## Decisiones tomadas

| Decisión | Opción elegida | Por qué |
|---|---|---|
| Canal | Telegram Bot API | Sin ventana de 24h ni plantillas aprobadas, gratis, sin verificación de negocio |
| Backend del bot | Python + `python-telegram-bot` (long polling) | Reutiliza la lógica ya prototipada, no requiere HTTPS público |
| Autenticación | OTP (código de 6 dígitos) enviado al correo institucional | No depende de que el alumno tenga Gmail; todo ocurre dentro del chat, sin navegador ni servicio web aparte |
| Envío del código | Resend | Servicio simple de envío de correo, tier gratuito suficiente para el MVP |
| Base de datos | Neon (Postgres) | Gratis, serverless, fácil de conectar por connection string |
| ORM | SQLAlchemy + Alembic | Estándar en Python, funciona en el bot, soporta migraciones |
| Deploy | Render | Un solo servicio: Background Worker para el bot |
| IA conversacional | DeepSeek API, con fallback a knowledge base local | Control de costos: solo se llama a DeepSeek si la KB local no tiene match |

> Nota: al usar OTP en vez de Google OAuth, **ya no se necesita un servicio FastAPI ni HTTPS público** — todo el flujo de vinculación ocurre dentro de la conversación de Telegram. Esto simplifica el deploy a un solo servicio en Render.

## Arquitectura general

```
                    ┌─────────────────────────┐
                    │   Telegram (alumno)      │
                    └───────────┬──────────────┘
                                │ long polling
                    ┌───────────▼──────────────┐
                    │   Bot (Render: Worker)    │
                    │   python-telegram-bot     │
                    │   ├── handlers/           │
                    │   │   └── vincular_handler│
                    │   ├── services/           │
                    │   │   ├── deepseek_service│
                    │   │   ├── knowledge_base  │
                    │   │   ├── otp_service     │
                    │   │   └── reminder_service│
                    │   └── jobs/reminder_job   │
                    └──────┬─────────────┬──────┘
                            │ SQLAlchemy   │ Resend API
                    ┌───────▼──────┐  ┌────▼──────────────┐
                    │ Neon         │  │ Correo institucional│
                    │ (Postgres)   │  │ del alumno           │
                    │ alumnos      │  └───────────────────┘
                    │ vinculaciones│
                    │ otp_codigos  │
                    │ recordatorios│
                    └──────────────┘
```

## Esquema de base de datos (SQLAlchemy)

* **alumnos** — código, email institucional, nombre, carrera, ciclo. Fuente de verdad de quién puede vincularse (hardcodeada al inicio, luego sincronizada con el sistema real de Tecsup).
* **vinculaciones** — `chat_id` (único) ↔ `alumno_id`, fecha de vinculación. Una vez creada, el bot identifica al alumno automáticamente en cada mensaje.
* **otp_codigos** — chat_id, alumno_id (candidato), código generado, fecha de expiración, intentos fallidos. Se borra o marca como usado tras la validación.
* **recordatorios** — alumno_id, texto, fecha/hora de disparo, estado (`pendiente` / `enviado`).
* **knowledge_base_cache** (opcional, fase 2) — preguntas frecuentes ya resueltas por DeepSeek, para no volver a llamar a la API.

## Flujo de autenticación (OTP vía Resend)

1. Alumno manda `/vincular` en Telegram.
2. Bot pide su código de alumno (ej. "escribe tu código, ej. T12345").
3. Backend busca ese código en la tabla `alumnos`.
   * No existe → responde "código no encontrado, verifica o contacta a...".
   * Existe → continúa.
4. Backend genera un código aleatorio de 6 dígitos (usando `secrets`, no `random`), lo guarda en `otp_codigos` junto al `chat_id` y una expiración de 5-10 minutos.
5. Se envía ese código, vía **Resend**, al correo institucional que ya estaba registrado para ese alumno — nunca a un correo que el alumno escriba libremente en el chat.
6. Bot le dice: "Te mandamos un código a tu correo institucional, escríbelo aquí para confirmar".
7. Alumno responde con el código recibido.
8. Backend valida: coincide, no expiró, y no se agotaron los intentos (máx. 3, luego hay que pedir uno nuevo).
9. Si es válido → se crea/actualiza `vinculaciones` (chat_id ↔ alumno) y se borra el OTP usado.
10. De ahí en adelante, cada mensaje del `chat_id` se resuelve automáticamente al alumno correspondiente.

## Flujo conversacional

1. Mensaje libre del alumno llega al bot.
2. Backend busca en la knowledge base local (offline, respuesta inmediata si hay match).
3. Si no hay match confiable → se llama a DeepSeek con system prompt de Tecsup + contexto del alumno (nombre, carrera, ciclo).
4. Respuesta se cachea en la KB local para consultas similares futuras.
5. Rate limiting por alumno para controlar costos de la API.

## Flujo de recordatorios

1. Job periódico (`JobQueue` de `python-telegram-bot`, corre cada pocos minutos) revisa la tabla `recordatorios` por vencer.
2. Por cada uno pendiente y a tiempo → `bot.send_message(chat_id=..., text=...)`.
3. Se marca como `enviado` en la BD para no duplicar avisos si el proceso se reinicia.
4. Sin restricción de ventana horaria (a diferencia de WhatsApp).

## Deploy en Render

* **Bot** → Background Worker, comando `python main.py`.
* Variables de entorno: `TELEGRAM_BOT_TOKEN`, `DATABASE_URL` (Neon), `RESEND_API_KEY`, `DEEPSEEK_API_KEY`.
* Un solo servicio — no se necesita Web Service ni HTTPS público para el MVP.

## Pendientes / próximos pasos

1. Crear proyecto en Neon, definir modelos con SQLAlchemy, generar migración inicial con Alembic.
2. Cargar datos de prueba hardcodeados en `alumnos`.
3. Crear cuenta en Resend y sacar el API key.
4. Implementar `otp_service.py`: generación, envío por Resend, validación con expiración e intentos.
5. Implementar `vincular_handler.py`: conversación de vinculación (pedir código → pedir OTP → confirmar).
6. Probar el flujo completo en local.
7. Deploy del bot en Render (Background Worker).
8. Reemplazar la knowledge base hardcodeada por la integración real con DeepSeek.
9. Implementar el job de recordatorios con persistencia en BD.
10. Cuando haya acceso a la API/BD real de Tecsup, sincronizar la tabla `alumnos` desde ahí en vez de datos hardcodeados.
