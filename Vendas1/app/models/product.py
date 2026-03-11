from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)

    code = Column(String, nullable=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(String, nullable=True)

    unit = Column(String, nullable=True, default="un")
    weight = Column(String, nullable=True)

    price = Column(Float, nullable=False, default=0.0)

    stock = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=0)

    image = Column(String, nullable=True)

    active = Column(Boolean, nullable=False, default=True)