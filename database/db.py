"""Conexión a la base de datos (Neon Postgres) vía SQLAlchemy."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "Falta la variable de entorno DATABASE_URL. "
        "Copia .env.example a .env y coloca el connection string de Neon."
    )

# Neon a veces entrega el connection string entre comillas simples; se limpian
# por si acaso quedaron pegadas al copiar/pegar.
DATABASE_URL = DATABASE_URL.strip("'").strip('"')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_session():
    """Devuelve una nueva sesión. Quien la use es responsable de cerrarla."""
    return SessionLocal()
