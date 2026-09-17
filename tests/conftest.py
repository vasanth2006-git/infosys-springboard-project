import sys
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
import models
from main import app, hash_password, ADMIN_SESSION_VAL

# -------------------------------------------------------------
# Isolated In-Memory SQLite Test Database Engine
# -------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Register MySQL-compatible scalar IF(cond, a, b) function in SQLite
@event.listens_for(test_engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
    dbapi_connection.create_function("IF", 3, lambda cond, a, b: a if cond else b)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all schema tables in test SQLite database once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db():
    """Provide a fresh, isolated database session per test with automatic cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """FastAPI TestClient with dependency override pointing to isolated test DB."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()

# -------------------------------------------------------------
# Test Seed Fixtures
# -------------------------------------------------------------
@pytest.fixture
def admin_cookies():
    """Valid administrator session cookie."""
    return {"admin_session": ADMIN_SESSION_VAL}

@pytest.fixture
def approved_vendor(db):
    """Pre-seeded approved vendor account."""
    vendor = models.Vendor(
        email="approved@shopsense.com",
        full_name="Alice Johnson",
        business_name="Apex Retail Co",
        password_hash=hash_password("password123"),
        phone_number="+1 555-0100",
        business_address="100 Innovation Way",
        status="Approved"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor

@pytest.fixture
def pending_vendor(db):
    """Pre-seeded pending vendor account."""
    vendor = models.Vendor(
        email="pending@shopsense.com",
        full_name="Bob Smith",
        business_name="Craft Goods",
        password_hash=hash_password("password123"),
        phone_number="+1 555-0101",
        business_address="200 Market St",
        status="Pending"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor

@pytest.fixture
def suspended_vendor(db):
    """Pre-seeded suspended vendor account."""
    vendor = models.Vendor(
        email="suspended@shopsense.com",
        full_name="Charlie Davis",
        business_name="Urban Wear",
        password_hash=hash_password("password123"),
        phone_number="+1 555-0102",
        business_address="300 Fashion Blvd",
        status="Suspended"
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor

@pytest.fixture
def sample_product(db, approved_vendor):
    """Pre-seeded product owned by approved vendor."""
    product = models.Product(
        name="Pro Wireless Headphones X2",
        category="Electronics",
        price=149.99,
        stock=25,
        image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        description="Experience high-fidelity audio with active noise cancellation.",
        vendor_email=approved_vendor.email
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@pytest.fixture
def sample_customer(db):
    """Pre-seeded customer record."""
    customer = models.Customer(
        name="John Doe",
        total_spend=1250.0
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer
