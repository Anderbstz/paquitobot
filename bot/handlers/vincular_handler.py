"""Vinculación chat_id <-> alumno.

Versión simplificada del flujo del plan (paquitobot-plan.md): por ahora
solo se pide el código de alumno y se valida contra la tabla `alumnos`.
La verificación por OTP al correo institucional (vía Resend) es el
siguiente paso pendiente del plan, todavía no implementado aquí.
"""

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database.db import SessionLocal
from database.models import Alumno, Vinculacion

ESPERANDO_CODIGO = 1


async def vincular_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Vamos a vincular tu cuenta ✍️\n"
        "Escribe tu código de alumno (ej. 111111), o /cancelar para salir."
    )
    return ESPERANDO_CODIGO


async def vincular_recibir_codigo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    codigo = update.message.text.strip()
    chat_id = update.effective_chat.id

    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter_by(codigo=codigo).first()
        if not alumno:
            await update.message.reply_text(
                "No encontré ningún alumno con ese código. Verifica e "
                "inténtalo de nuevo, o escribe /cancelar."
            )
            return ESPERANDO_CODIGO

        vinculacion = session.query(Vinculacion).filter_by(chat_id=chat_id).first()
        if vinculacion:
            vinculacion.alumno_id = alumno.id
        else:
            vinculacion = Vinculacion(chat_id=chat_id, alumno_id=alumno.id)
            session.add(vinculacion)
        session.commit()

        await update.message.reply_markdown(
            f"✅ ¡Listo, *{alumno.nombre}*! Tu cuenta quedó vinculada.\n"
            "Ya puedes usar /cursos y /horario."
        )
        return ConversationHandler.END
    finally:
        session.close()


async def vincular_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vinculación cancelada.")
    return ConversationHandler.END


vincular_conversation = ConversationHandler(
    entry_points=[CommandHandler("vincular", vincular_start)],
    states={
        ESPERANDO_CODIGO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, vincular_recibir_codigo)
        ],
    },
    fallbacks=[CommandHandler("cancelar", vincular_cancelar)],
)
