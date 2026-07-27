"""Modelos SQLAlchemy del MVP.

Ver paquitobot-plan.md para el esquema completo. Se modelan alumnos,
cursos, horarios, la matrícula (alumno <-> curso), la vinculación
chat_id <-> alumno y los códigos OTP usados para verificar esa
vinculación. Los `recordatorios` se agregarán en un paso posterior.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.db import Base


class Alumno(Base):
    __tablename__ = "alumnos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    carrera = Column(String(150))
    ciclo = Column(Integer)

    vinculacion = relationship(
        "Vinculacion", back_populates="alumno", uselist=False, cascade="all, delete-orphan"
    )
    matriculas = relationship("Matricula", back_populates="alumno", cascade="all, delete-orphan")


class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    ciclo = Column(Integer)
    docente = Column(String(150))

    horarios = relationship("Horario", back_populates="curso", cascade="all, delete-orphan")
    matriculas = relationship("Matricula", back_populates="curso", cascade="all, delete-orphan")


class Horario(Base):
    __tablename__ = "horarios"

    id = Column(Integer, primary_key=True)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    dia_semana = Column(String(20), nullable=False)  # Lunes, Martes, ...
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    aula = Column(String(50))

    curso = relationship("Curso", back_populates="horarios")


class Matricula(Base):
    """Relación N:N entre alumno y curso (cursos en los que está matriculado)."""

    __tablename__ = "matriculas"
    __table_args__ = (UniqueConstraint("alumno_id", "curso_id", name="uq_alumno_curso"),)

    id = Column(Integer, primary_key=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    curso_id = Column(Integer, ForeignKey("cursos.id"), nullable=False)

    alumno = relationship("Alumno", back_populates="matriculas")
    curso = relationship("Curso", back_populates="matriculas")


class Vinculacion(Base):
    """chat_id de Telegram <-> alumno. Se crea al validar el OTP."""

    __tablename__ = "vinculaciones"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    fecha_vinculacion = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    alumno = relationship("Alumno", back_populates="vinculacion")


class OtpCodigo(Base):
    """Código OTP pendiente de validación para vincular chat_id <-> alumno.

    Se crea al pedir el código de alumno en /vincular y se envía por
    Resend al correo institucional. Se borra al validarse, expirar o
    agotar los intentos.
    """

    __tablename__ = "otp_codigos"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"), nullable=False)
    codigo = Column(String(6), nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    creado_en = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    alumno = relationship("Alumno")
