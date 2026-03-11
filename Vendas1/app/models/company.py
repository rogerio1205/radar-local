from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    legal_name = Column(String, nullable=True)
    cnpj = Column(String, nullable=True)

    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)

    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    address = Column(String, nullable=True)

    website = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    map_link = Column(String, nullable=True)

    description = Column(String, nullable=True)
    specialties = Column(String, nullable=True)

    pix_key = Column(String, nullable=True)

    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)

    logo = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())