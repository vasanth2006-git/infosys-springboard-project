import uvicorn
import logging
from app.database import Base, Engine, SessionLocal
from app.models import Vendor, Product, Transaction
from app.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shopsense")

def seed_demo_data():
    """Seed initial sample vendors, products, and transactions to demonstrate ShopSense immediately."""
    db = SessionLocal()
    try:
        if db.query(Vendor).count() == 0:
            logger.info("Seeding demo vendors for ShopSense...")
            v1 = Vendor(
                full_name="Alice Johnson",
                business_name="Apex Electronics",
                email="alice@apex.com",
                password_hash=hash_password("password123"),
                phone="+1 555-0101",
                address="742 Evergreen Terrace, Springfield",
                status="Pending"
            )
            v2 = Vendor(
                full_name="Bob Smith",
                business_name="Craft & Co. Goods",
                email="bob@craftco.com",
                password_hash=hash_password("password123"),
                phone="+1 555-0102",
                address="100 Market St, San Francisco",
                status="Approved"
            )
            v3 = Vendor(
                full_name="Charlie Davis",
                business_name="Urban Wear Threads",
                email="charlie@urbanwear.com",
                password_hash=hash_password("password123"),
                phone="+1 555-0103",
                address="55 Broadway, New York",
                status="Suspended"
            )
            db.add_all([v1, v2, v3])
            db.commit()
            db.refresh(v2)

            logger.info("Seeding demo products and transactions for approved vendor (Bob Smith)...")
            p1 = Product(
                vendor_id=v2.id,
                name="Handcrafted Leather Journal",
                category="Books & Stationery",
                price=34.99,
                stock=28,
                image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&auto=format&fit=crop&q=80",
                description="Premium refillable leather journal with unlined cotton pages, perfect for daily notes, sketches, and travel memories.",
                status="Published"
            )
            p2 = Product(
                vendor_id=v2.id,
                name="Artisanal Ceramic Coffee Mug",
                category="Home & Living",
                price=22.50,
                stock=45,
                image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=300&auto=format&fit=crop&q=80",
                description="Ergonomically designed hand-thrown ceramic mug with satin glaze. Microwave and dishwasher safe.",
                status="Published"
            )
            p3 = Product(
                vendor_id=v2.id,
                name="Minimalist Wooden Desk Organizer",
                category="Home & Living",
                price=49.00,
                stock=12,
                image_url="https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=300&auto=format&fit=crop&q=80",
                description="Sleek solid walnut wood desk tray for pens, stationery, phone, and daily workspace accessories.",
                status="Published"
            )
            p4 = Product(
                vendor_id=v2.id,
                name="Organic Cotton Tote Bag",
                category="Fashion & Apparel",
                price=18.00,
                stock=60,
                image_url="https://images.unsplash.com/photo-1597484661643-2f5fef640dd1?w=300&auto=format&fit=crop&q=80",
                description="Heavy-duty 100% organic cotton canvas tote featuring reinforced stitching and spacious interior pocket.",
                status="Published"
            )

            db.add_all([p1, p2, p3, p4])
            db.commit()

            # Seed transactions for Bob Smith
            t1 = Transaction(vendor_id=v2.id, product_id=p1.id, transaction_code="TXN-1001", items_sold=12, total_revenue=419.88)
            t2 = Transaction(vendor_id=v2.id, product_id=p2.id, transaction_code="TXN-1002", items_sold=20, total_revenue=450.00)
            t3 = Transaction(vendor_id=v2.id, product_id=p3.id, transaction_code="TXN-1003", items_sold=8, total_revenue=392.00)
            t4 = Transaction(vendor_id=v2.id, product_id=p4.id, transaction_code="TXN-1004", items_sold=15, total_revenue=270.00)

            db.add_all([t1, t2, t3, t4])
            db.commit()
            logger.info("Demo data successfully seeded!")
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create DB tables
    Base.metadata.create_all(bind=Engine)
    seed_demo_data()

    print("\n" + "="*60)
    print("🚀 ShopSense FastAPI Server is Starting!")
    print("   Access Login Page:           http://127.0.0.1:8000/login")
    print("   Access Vendor Registration:  http://127.0.0.1:8000/register")
    print("   Access Vendor Dashboard:     http://127.0.0.1:8000/vendor/dashboard")
    print("   Access Admin Dashboard:      http://127.0.0.1:8000/admin/dashboard")
    print("   Approved Vendor Login:       bob@craftco.com / password123")
    print("   Admin Credentials:           admin@gmail.com / admin123")
    print("="*60 + "\n")

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
