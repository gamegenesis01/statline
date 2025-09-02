from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.database_url, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
