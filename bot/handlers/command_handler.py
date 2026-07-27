"""Comandos del bot.

/cursos y /horario ahora consultan la base de datos (ver
bot/services/academic_service.py) en vez de devolver texto fijo.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.academic_service import listar_cursos, listar_horario

TEXTO_AYUDA = (
    "*Comandos disponibles:*\n"
    "/start — Iniciar conversación con PaquitoBot\n"
    "/ayuda — Ver esta lista de comandos\n"
    "/vincular — Vincular tu cuenta con tu código de alumno\n"
    "/cursos — Ver tus cursos matriculados\n"
    "/horario — Ver tu horario de clases\n\n"
    "También puedes escribirme directamente preguntas sobre matrícula, "
    "pagos, becas, exámenes, biblioteca o soporte técnico."
)


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_markdown(TEXTO_AYUDA)


async def cursos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    respuesta = listar_cursos(update.effective_chat.id)
    await update.message.reply_markdown(respuesta)


async def horario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    respuesta = listar_horario(update.effective_chat.id)
    await update.message.reply_markdown(respuesta)
