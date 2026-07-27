"""Handler para /start.

En el MVP actual no hay base de datos, así que no se vincula
realmente el chat_id a un alumno: solo se saluda usando el nombre
de Telegram del usuario.
"""

from telegram import Update
from telegram.ext import ContextTypes

MENSAJE_BIENVENIDA = (
    "¡Hola {nombre}! 👋 Soy *PaquitoBot*, el asistente virtual de Tecsup.\n\n"
    "Usa /vincular con tu código de alumno para que pueda mostrarte tus "
    "cursos y horario. También respondo preguntas frecuentes sobre "
    "matrícula, pagos, becas, exámenes, biblioteca y soporte técnico. "
    "Usa /ayuda para ver todos los comandos."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    nombre = update.effective_user.first_name if update.effective_user else "alumno"
    await update.message.reply_markdown(MENSAJE_BIENVENIDA.format(nombre=nombre))
