"""Consultas académicas (cursos, horarios) contra la base de datos.

Reemplaza los textos hardcodeados que antes vivían en command_handler.py.
Resuelve al alumno a partir del chat_id (requiere haber usado /vincular).
"""

from __future__ import annotations

from database.db import SessionLocal
from database.models import Curso, Horario, Matricula, Vinculacion

DIAS_ORDEN = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

MENSAJE_NO_VINCULADO = (
    "🔒 Aún no vinculaste tu cuenta. Usa /vincular y escribe tu código de "
    "alumno para poder consultar tus cursos y horarios."
)


def _obtener_vinculacion(session, chat_id: int) -> Vinculacion | None:
    return session.query(Vinculacion).filter_by(chat_id=chat_id).first()


def listar_cursos(chat_id: int) -> str:
    session = SessionLocal()
    try:
        vinculacion = _obtener_vinculacion(session, chat_id)
        if not vinculacion:
            return MENSAJE_NO_VINCULADO

        cursos = (
            session.query(Curso)
            .join(Matricula, Matricula.curso_id == Curso.id)
            .filter(Matricula.alumno_id == vinculacion.alumno_id)
            .order_by(Curso.nombre)
            .all()
        )
        if not cursos:
            return "No tienes cursos matriculados registrados por ahora."

        lineas = ["📚 *Tus cursos matriculados:*"]
        for curso in cursos:
            docente = curso.docente or "docente por asignar"
            lineas.append(f"• {curso.nombre} ({curso.codigo}) — {docente}")
        return "\n".join(lineas)
    finally:
        session.close()


def listar_horario(chat_id: int) -> str:
    session = SessionLocal()
    try:
        vinculacion = _obtener_vinculacion(session, chat_id)
        if not vinculacion:
            return MENSAJE_NO_VINCULADO

        horarios = (
            session.query(Horario)
            .join(Curso, Horario.curso_id == Curso.id)
            .join(Matricula, Matricula.curso_id == Curso.id)
            .filter(Matricula.alumno_id == vinculacion.alumno_id)
            .all()
        )
        if not horarios:
            return "No encontré horarios para tus cursos todavía."

        def orden(h: Horario):
            dia_idx = DIAS_ORDEN.index(h.dia_semana) if h.dia_semana in DIAS_ORDEN else 99
            return (dia_idx, h.hora_inicio)

        horarios.sort(key=orden)

        lineas = ["📅 *Tu horario:*"]
        for h in horarios:
            inicio = h.hora_inicio.strftime("%H:%M")
            fin = h.hora_fin.strftime("%H:%M")
            aula = h.aula or "por confirmar"
            lineas.append(f"• {h.dia_semana} {inicio}–{fin} — {h.curso.nombre} (aula {aula})")
        return "\n".join(lineas)
    finally:
        session.close()
