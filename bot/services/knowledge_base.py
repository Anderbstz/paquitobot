"""Knowledge base local (hardcodeada) para el MVP.

Cuando exista base de datos / DeepSeek, esta capa se puede reemplazar
sin tocar los handlers, ya que solo se expone `buscar_respuesta`.
"""

from __future__ import annotations

# Cada entrada: (lista de palabras clave, respuesta)
# El match es simple: si alguna keyword aparece en el mensaje del alumno.
FAQ: list[tuple[list[str], str]] = [
    (
        ["horario", "horarios"],
        "📅 Los horarios de clases los encuentras en el portal del alumno, "
        "sección 'Mi Horario'. Si tienes un cruce de horario, repórtalo a "
        "Registros Académicos.",
    ),
    (
        ["matricula", "matrícula", "inscripcion", "inscripción"],
        "📝 El proceso de matrícula se realiza desde el portal Tecsup. "
        "Recuerda estar al día con tus pagos para poder matricularte.",
    ),
    (
        ["pago", "pagos", "pension", "pensión", "boleta"],
        "💳 Puedes revisar y pagar tus pensiones desde el portal de pagos "
        "de Tecsup o en los bancos afiliados (BCP, BBVA, Interbank).",
    ),
    (
        ["beca", "becas"],
        "🎓 La información de becas y descuentos está en la sección de "
        "Bienestar Estudiantil del portal. También puedes preguntar en "
        "Admisión.",
    ),
    (
        ["examen", "examenes", "exámenes", "evaluacion", "evaluación"],
        "📖 Las fechas de exámenes se publican en el calendario académico "
        "del ciclo. Revisa tu portal para fechas específicas por curso.",
    ),
    (
        ["biblioteca"],
        "📚 La biblioteca está abierta de lunes a sábado. Puedes reservar "
        "salas de estudio desde el portal de servicios.",
    ),
    (
        ["soporte", "ayuda tecnica", "ayuda técnica", "clave", "contraseña", "contrasena"],
        "🛠️ Para temas de soporte técnico (claves, accesos, correo "
        "institucional) contacta a Mesa de Ayuda: soporte@tecsup.edu.pe",
    ),
]

FALLBACK_RESPUESTA = (
    "🤔 No tengo una respuesta exacta para eso todavía. "
    "Te recomiendo consultarlo por el canal oficial de Tecsup "
    "o escribir a informes@tecsup.edu.pe.\n\n"
    "(Muy pronto podré responder preguntas más complejas 🚀)"
)


def buscar_respuesta(mensaje: str) -> str:
    """Busca una respuesta hardcodeada según palabras clave en el mensaje."""
    texto = mensaje.lower()

    for keywords, respuesta in FAQ:
        if any(kw in texto for kw in keywords):
            return respuesta

    return FALLBACK_RESPUESTA
