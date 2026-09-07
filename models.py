from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, event, text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    email = Column(String(150), primary_key=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    business_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    business_address = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Pending") # Pending, Approved, Suspended

    products = relationship("Product", back_populates="vendor", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "email": self.email,
            "full_name": self.full_name,
            "business_name": self.business_name,
            "phone_number": self.phone_number,
            "business_address": self.business_address,
            "status": self.status
        }

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True) # AI-generated description
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    image_url = Column(Text, nullable=True)
    vendor_email = Column(String(150), ForeignKey("vendors.email"), nullable=False)

    vendor = relationship("Vendor", back_populates="products")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    vendor_email = Column(String(150), ForeignKey("vendors.email"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    amount = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    total_spend = Column(Float, nullable=False, default=0.0)

    # Future integration mapping:
    # transactions = relationship("Transaction", back_populates="customer")

    @property
    def segment(self) -> str:
        if self.total_spend >= 1000:
            return "Premium Customer"
        elif self.total_spend >= 100:
            return "Regular Customer"
        else:
            return "New Customer"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "total_spend": self.total_spend,
            "segment": self.segment
        }

@event.listens_for(Transaction, 'after_insert')
def reduce_stock_on_transaction(mapper, connection, target):
    if target.product_id:
        connection.execute(
            text("UPDATE products SET stock = IF(stock >= :qty, stock - :qty, 0) WHERE id = :pid"),
            {"qty": target.quantity, "pid": target.product_id}
        )

