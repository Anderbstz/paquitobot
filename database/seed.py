"""Crea las tablas (si no existen) y carga datos de prueba hardcodeados.

Uso:
    python -m database.seed

Esto reemplaza los datos hardcodeados que antes vivían en
bot/handlers/command_handler.py. Cuando haya acceso a la API/BD real
de Tecsup, este script se reemplaza por una sincronización real.
"""

from datetime import datetime

from database.db import Base, SessionLocal, engine
from database.models import Alumno, Curso, Horario, Matricula

ALUMNO_PRUEBA = {
    "codigo": "111111",
    "email": "ithalo.bustamante@tecsup.edu.pe",
    "nombre": "Ithalo Bustamante",
    "carrera": "Diseño y Desarrollo de Software",
    "ciclo": 5,
}

CURSOS_PRUEBA = [
    {
        "codigo": "DSW501",
        "nombre": "Programación Orientada a Objetos Avanzada",
        "ciclo": 5,
        "docente": "Ing. Carla Ramírez",
        "horarios": [
            ("Lunes", "08:00", "10:00", "A-301"),
            ("Miércoles", "08:00", "10:00", "A-301"),
        ],
    },
    {
        "codigo": "DSW502",
        "nombre": "Base de Datos II",
        "ciclo": 5,
        "docente": "Ing. Jorge Salas",
        "horarios": [
            ("Martes", "10:00", "12:00", "Lab-204"),
        ],
    },
    {
        "codigo": "DSW503",
        "nombre": "Redes de Computadoras",
        "ciclo": 5,
        "docente": "Ing. Paola Vidal",
        "horarios": [
            ("Jueves", "14:00", "16:00", "Lab-108"),
        ],
    },
    {
        "codigo": "ENG204",
        "nombre": "Inglés Técnico IV",
        "ciclo": 5,
        "docente": "Lic. Andrea Torres",
        "horarios": [
            ("Viernes", "16:00", "18:00", "B-105"),
        ],
    },
]


def _hora(texto: str):
    return datetime.strptime(texto, "%H:%M").time()


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        alumno = session.query(Alumno).filter_by(codigo=ALUMNO_PRUEBA["codigo"]).first()
        if not alumno:
            alumno = Alumno(**ALUMNO_PRUEBA)
            session.add(alumno)
            session.flush()
            print(f"Alumno creado: {alumno.nombre} ({alumno.codigo})")
        else:
            print(f"Alumno ya existía: {alumno.nombre} ({alumno.codigo})")

        for data in CURSOS_PRUEBA:
            curso = session.query(Curso).filter_by(codigo=data["codigo"]).first()
            if not curso:
                curso = Curso(
                    codigo=data["codigo"],
                    nombre=data["nombre"],
                    ciclo=data["ciclo"],
                    docente=data["docente"],
                )
                session.add(curso)
                session.flush()

                for dia, inicio, fin, aula in data["horarios"]:
                    session.add(
                        Horario(
                            curso_id=curso.id,
                            dia_semana=dia,
                            hora_inicio=_hora(inicio),
                            hora_fin=_hora(fin),
                            aula=aula,
                        )
                    )
                print(f"Curso creado: {curso.nombre}")

            ya_matriculado = (
                session.query(Matricula)
                .filter_by(alumno_id=alumno.id, curso_id=curso.id)
                .first()
            )
            if not ya_matriculado:
                session.add(Matricula(alumno_id=alumno.id, curso_id=curso.id))

        session.commit()
        print("Seed completado correctamente.")
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
