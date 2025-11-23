from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from .db import get_session


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session
