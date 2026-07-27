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

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

if not RESEND_API_KEY:
    raise RuntimeError(
        "Falta la variable de entorno RESEND_API_KEY. "
        "Créala en https://resend.com y colócala en tu .env."
    )

# Remitente de los correos con el OTP. Debe usar un dominio verificado en
# Resend (por defecto, anderbstz.lat).
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "PaquitoBot <bot@anderbstz.lat>")
