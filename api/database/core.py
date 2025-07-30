from typing import Annotated
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import Session, DeclarativeBase
from fastapi import Depends
from api.config import DATABASE_URI



engine = create_engine(DATABASE_URI)


def get_session():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


DbSession = Annotated[Session, Depends(get_session)]


class Base(DeclarativeBase):
    pass
