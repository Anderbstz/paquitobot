"""Punto de entrada del bot. Usa long polling (sin necesidad de HTTPS público)."""

import logging

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers.command_handler import ayuda, cursos, horario
from bot.handlers.message_handler import responder_mensaje
from bot.handlers.start_handler import start
from bot.handlers.vincular_handler import vincular_conversation

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(vincular_conversation)
    app.add_handler(CommandHandler("cursos", cursos))
    app.add_handler(CommandHandler("horario", horario))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensaje))

    logging.info("PaquitoBot iniciado. Esperando mensajes...")
    app.run_polling()


if __name__ == "__main__":
    main()
