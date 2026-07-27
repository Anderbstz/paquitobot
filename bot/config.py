"""Configuración del bot. Lee credenciales desde variables de entorno."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "Falta la variable de entorno TELEGRAM_BOT_TOKEN. "
        "Copia .env.example a .env y coloca el token de @BotFather."
    )
