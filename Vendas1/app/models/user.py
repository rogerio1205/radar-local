from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    region = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

    roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )