"""Vinculación chat_id <-> alumno, con verificación por OTP (Resend).

Flujo:
1. /vincular → pide el código de alumno.
2. Se busca el código en `alumnos`. Si existe, se genera un OTP y se
   envía al correo institucional ya registrado (nunca a uno que el
   alumno escriba en el chat).
3. El alumno responde con el código recibido por correo.
4. Si es válido (no expiró, no se agotaron los intentos) se crea/actualiza
   la vinculación chat_id <-> alumno.
"""

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.services.otp_service import ResultadoOtp, enmascarar_email, generar_y_enviar_otp, validar_otp
from database.db import SessionLocal
from database.models import Alumno, Vinculacion

ESPERANDO_CODIGO_ALUMNO, ESPERANDO_OTP = range(2)


async def vincular_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Vamos a vincular tu cuenta ✍️\n"
        "Escribe tu código de alumno (ej. 111111), o /cancelar para salir."
    )
    return ESPERANDO_CODIGO_ALUMNO


async def recibir_codigo_alumno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
            return ESPERANDO_CODIGO_ALUMNO

        correo_oculto = enmascarar_email(alumno.email)
    finally:
        session.close()

    try:
        generar_y_enviar_otp(chat_id, alumno)
    except Exception:
        await update.message.reply_text(
            "⚠️ Tuve un problema enviando el correo con el código. "
            "Intenta de nuevo en unos minutos con /vincular."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Te envié un código de 6 dígitos a tu correo institucional "
        f"({correo_oculto}). Escríbelo aquí para confirmar.\n\n"
        "Tienes 10 minutos y 3 intentos. /cancelar para salir."
    )
    return ESPERANDO_OTP


async def recibir_otp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    codigo_ingresado = update.message.text.strip()

    resultado, extra = validar_otp(chat_id, codigo_ingresado)

    if resultado == ResultadoOtp.OK:
        alumno_id = extra
        session = SessionLocal()
        try:
            vinculacion = session.query(Vinculacion).filter_by(chat_id=chat_id).first()
            if vinculacion:
                vinculacion.alumno_id = alumno_id
            else:
                session.add(Vinculacion(chat_id=chat_id, alumno_id=alumno_id))
            session.commit()

            alumno = session.get(Alumno, alumno_id)
            nombre = alumno.nombre if alumno else "alumno"
        finally:
            session.close()

        await update.message.reply_markdown(
            f"✅ ¡Listo, *{nombre}*! Tu cuenta quedó vinculada y verificada.\n"
            "Ya puedes usar /cursos y /horario."
        )
        return ConversationHandler.END

    if resultado == ResultadoOtp.INCORRECTO:
        intentos_restantes = extra
        await update.message.reply_text(
            f"Código incorrecto. Te quedan {intentos_restantes} intento(s)."
        )
        return ESPERANDO_OTP

    if resultado == ResultadoOtp.EXPIRADO:
        await update.message.reply_text(
            "⏰ El código expiró. Usa /vincular de nuevo para pedir uno nuevo."
        )
        return ConversationHandler.END

    if resultado == ResultadoOtp.SIN_INTENTOS:
        await update.message.reply_text(
            "❌ Agotaste los intentos. Usa /vincular de nuevo para pedir un "
            "código nuevo."
        )
        return ConversationHandler.END

    # NO_EXISTE
    await update.message.reply_text(
        "No encontré un código pendiente para ti. Usa /vincular para "
        "empezar de nuevo."
    )
    return ConversationHandler.END


async def vincular_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vinculación cancelada.")
    return ConversationHandler.END


vincular_conversation = ConversationHandler(
    entry_points=[CommandHandler("vincular", vincular_start)],
    states={
        ESPERANDO_CODIGO_ALUMNO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_codigo_alumno)
        ],
        ESPERANDO_OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_otp)],
    },
    fallbacks=[CommandHandler("cancelar", vincular_cancelar)],
)
