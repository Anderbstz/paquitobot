"""Generación, envío (Resend) y validación de códigos OTP.

Flujo (ver paquitobot-plan.md):
1. Se genera un código de 6 dígitos con `secrets` (no `random`).
2. Se guarda en `otp_codigos` junto al chat_id, con expiración de
   `DURACION_OTP_MINUTOS`.
3. Se envía por Resend al correo institucional del alumno (nunca a un
   correo que el alumno escriba libremente en el chat).
4. Al validarse se permiten hasta `MAX_INTENTOS` intentos antes de
   invalidar el código y pedir uno nuevo.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import resend

from bot.config import RESEND_API_KEY, RESEND_FROM_EMAIL
from database.db import SessionLocal
from database.models import Alumno, OtpCodigo

resend.api_key = RESEND_API_KEY

DURACION_OTP_MINUTOS = 10
MAX_INTENTOS = 3


class ResultadoOtp:
    OK = "ok"
    NO_EXISTE = "no_existe"
    EXPIRADO = "expirado"
    INCORRECTO = "incorrecto"
    SIN_INTENTOS = "sin_intentos"


def enmascarar_email(email: str) -> str:
    """it***@tecsup.edu.pe en vez de mostrar el correo completo en el chat."""
    local, _, dominio = email.partition("@")
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}{'*' * 3}@{dominio}"


def generar_y_enviar_otp(chat_id: int, alumno: Alumno) -> None:
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    expira_en = datetime.now(timezone.utc) + timedelta(minutes=DURACION_OTP_MINUTOS)

    session = SessionLocal()
    try:
        # Limpia cualquier OTP anterior de este chat antes de crear uno nuevo.
        session.query(OtpCodigo).filter_by(chat_id=chat_id).delete()
        session.add(
            OtpCodigo(
                chat_id=chat_id,
                alumno_id=alumno.id,
                codigo=codigo,
                expira_en=expira_en,
            )
        )
        session.commit()
    finally:
        session.close()

    _enviar_correo_otp(alumno.email, alumno.nombre, codigo)


def _enviar_correo_otp(destinatario: str, nombre: str, codigo: str) -> None:
    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [destinatario],
        "subject": "Tu código de verificación de PaquitoBot",
        "html": (
            f"<p>Hola {nombre},</p>"
            "<p>Tu código de verificación para vincular tu cuenta de "
            "Telegram con <b>PaquitoBot</b> es:</p>"
            f"<h2 style='letter-spacing:4px'>{codigo}</h2>"
            f"<p>Vence en {DURACION_OTP_MINUTOS} minutos. Si tú no "
            "solicitaste esto, puedes ignorar este correo.</p>"
        ),
    }
    resend.Emails.send(params)


def validar_otp(chat_id: int, codigo_ingresado: str) -> tuple[str, int | None]:
    """Valida el código. Devuelve (resultado, dato_extra).

    dato_extra es el alumno_id cuando el resultado es OK, o los intentos
    restantes cuando el resultado es INCORRECTO. En el resto de los casos
    es None.
    """
    session = SessionLocal()
    try:
        otp = session.query(OtpCodigo).filter_by(chat_id=chat_id).first()
        if not otp:
            return ResultadoOtp.NO_EXISTE, None

        expira_en = otp.expira_en
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expira_en:
            session.delete(otp)
            session.commit()
            return ResultadoOtp.EXPIRADO, None

        if otp.codigo != codigo_ingresado.strip():
            otp.intentos_fallidos += 1
            if otp.intentos_fallidos >= MAX_INTENTOS:
                session.delete(otp)
                session.commit()
                return ResultadoOtp.SIN_INTENTOS, None
            session.commit()
            return ResultadoOtp.INCORRECTO, MAX_INTENTOS - otp.intentos_fallidos

        alumno_id = otp.alumno_id
        session.delete(otp)
        session.commit()
        return ResultadoOtp.OK, alumno_id
    finally:
        session.close()
