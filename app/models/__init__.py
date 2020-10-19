

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ActiveUser(Base):
    __tablename__ = "active_user"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=False, nullable=False)
    username = Column(String(255), unique=True, nullable=False)
