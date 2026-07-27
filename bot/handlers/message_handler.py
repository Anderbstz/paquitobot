"""Handler para mensajes libres del alumno.

Por ahora solo consulta la knowledge base hardcodeada. Este es el
punto donde más adelante se enchufará DeepSeek como fallback.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.knowledge_base import buscar_respuesta


async def responder_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    respuesta = buscar_respuesta(update.message.text)
    await update.message.reply_text(respuesta)
