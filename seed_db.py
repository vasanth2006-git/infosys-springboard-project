import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the current directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models

def hash_password(password: str) -> str:
    import hashlib
    salt = "shopsense_secure_salt_string"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def seed_demo_transactions(db, vendor_email: str):
    products = db.query(models.Product).filter(models.Product.vendor_email == vendor_email).all()
    if not products:
        print("No products found for vendor. Cannot seed transactions.")
        return 0
        
    now = datetime.utcnow()
    
    # Clear existing transactions for this vendor to ensure clean, realistic demo data
    deleted_count = db.query(models.Transaction).filter(models.Transaction.vendor_email == vendor_email).delete()
    db.commit()
    print(f"Cleared {deleted_count} existing transactions for {vendor_email}.")
    
    inserted_count = 0
    
    # Monthly: past 12 months
    for m in range(1, 12):
        month_date = now - timedelta(days=m * 30 + random.randint(0, 15))
        for i, prod in enumerate(products):
            runs = 2 if i == 0 else (1 if random.random() > 0.5 else 0)
            for _ in range(runs):
                qty = random.randint(10, 20) if i == 0 else random.randint(1, 8)
                tx = models.Transaction(
                    vendor_email=vendor_email,
                    product_id=prod.id,
                    amount=prod.price * qty,
                    quantity=qty,
                    created_at=month_date
                )
                db.add(tx)
                inserted_count += 1
                
    # Weekly: past 4 weeks
    for w in range(1, 4):
        week_date = now - timedelta(weeks=w, days=random.randint(0, 5))
        for i, prod in enumerate(products):
            runs = 2 if i == 0 else (1 if random.random() > 0.4 else 0)
            for _ in range(runs):
                qty = random.randint(8, 15) if i == 0 else random.randint(1, 6)
                tx = models.Transaction(
                    vendor_email=vendor_email,
                    product_id=prod.id,
                    amount=prod.price * qty,
                    quantity=qty,
                    created_at=week_date
                )
                db.add(tx)
                inserted_count += 1
                
    # Daily: past 7 days
    for d in range(7):
        day_date = now - timedelta(days=d)
        for i, prod in enumerate(products):
            runs = 2 if i == 0 else (1 if random.random() > 0.3 else 0)
            for _ in range(runs):
                qty = random.randint(5, 12) if i == 0 else random.randint(1, 4)
                tx = models.Transaction(
                    vendor_email=vendor_email,
                    product_id=prod.id,
                    amount=prod.price * qty,
                    quantity=qty,
                    created_at=day_date
                )
                db.add(tx)
                inserted_count += 1
                
    db.commit()
    return inserted_count

def main():
    # Make sure tables exist and created_at column is present
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        
        with engine.begin() as conn:
            col_check = conn.execute(text("SHOW COLUMNS FROM transactions LIKE 'created_at';")).fetchone()
            if not col_check:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;"))
                print("Added created_at column to transactions table.")
    except Exception as e:
        print(f"Database setup error: {e}")
        return

    db = SessionLocal()
    try:
        # Seed customer data if missing
        if db.query(models.Customer).count() == 0:
            sample_customers = [
                models.Customer(name="John", total_spend=1250.0),
                models.Customer(name="David", total_spend=850.0),
                models.Customer(name="Sarah", total_spend=450.0),
                models.Customer(name="Alex", total_spend=75.0),
                models.Customer(name="Mike", total_spend=1200.0)
            ]
            db.add_all(sample_customers)
            db.commit()
            print("Seeded sample customer data.")
            
        # Seed vendor data if missing
        vendor_email = "vendor@gmail.com"
        vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_email).first()
        if not vendor:
            vendor = models.Vendor(
                email=vendor_email,
                full_name="Jane Doe",
                business_name="ShopSense Retail",
                password_hash=hash_password("vendor123"),
                phone_number="+1 (555) 019-2834",
                business_address="123 ShopSense Blvd, Suite 100",
                status="Approved"
            )
            db.add(vendor)
            db.commit()
            print(f"Seeded vendor: {vendor_email} (password: vendor123)")
            
        # Seed product data if missing
        if db.query(models.Product).filter(models.Product.vendor_email == vendor_email).count() == 0:
            sample_products = [
                models.Product(
                    name="Pro Wireless Headphones X2",
                    category="Electronics",
                    price=149.99,
                    stock=50,
                    image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&auto=format&fit=crop&q=60",
                    description="Experience high-fidelity audio with our Pro Wireless Headphones.",
                    vendor_email=vendor_email
                ),
                models.Product(
                    name="Ergonomic Office Mesh Chair",
                    category="Home & Kitchen",
                    price=199.00,
                    stock=30,
                    image_url="https://images.unsplash.com/photo-1580481072645-022f9a6dbf27?w=400&auto=format&fit=crop&q=60",
                    description="Breathable mesh ergonomic office chair.",
                    vendor_email=vendor_email
                ),
                models.Product(
                    name="Waterproof Trail Running Shoes",
                    category="Sports & Outdoors",
                    price=129.00,
                    stock=25,
                    image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&auto=format&fit=crop&q=60",
                    description="Conquer any terrain with these waterproof running shoes.",
                    vendor_email=vendor_email
                ),
                models.Product(
                    name="Minimalist Leather Wallet",
                    category="Apparel",
                    price=45.00,
                    stock=100,
                    image_url="https://images.unsplash.com/photo-1627124118303-624c89498a43?w=400&auto=format&fit=crop&q=60",
                    description="Slim leather card holder.",
                    vendor_email=vendor_email
                )
            ]
            db.add_all(sample_products)
            db.commit()
            print("Seeded 4 products for the vendor.")

        # Seed transactions
        inserted = seed_demo_transactions(db, vendor_email)
        print(f"\nSeeding complete! Successfully inserted {inserted} demo transactions into 'transactions' table.")
        
        # Verify and display counts
        total_tx = db.query(models.Transaction).filter(models.Transaction.vendor_email == vendor_email).count()
        print(f"Verification: Total transactions now stored in database for {vendor_email}: {total_tx}")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
