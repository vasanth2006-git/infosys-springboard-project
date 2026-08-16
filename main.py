import hashlib
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from database import engine, Base, get_db
import models

app = FastAPI(title="ShopSense Marketplace Portal", debug=True)

# Mount static and templates directory
# Ensure folders exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Admin credentials
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"
ADMIN_SESSION_VAL = "shopsense_admin_session_token_123"

# -------------------------------------------------------------
# Password Hashing Helpers (Pure Python, Zero Dependency)
# -------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = "shopsense_secure_salt_string"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# -------------------------------------------------------------
# Startup Event
# -------------------------------------------------------------
@app.on_event("startup")
def startup_db_init():
    # Automatically create tables in MySQL database on application startup
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error creating tables: {e}")
        
    # Explicitly enforce AUTO_INCREMENT and expand image_url column size to TEXT
    try:
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE products MODIFY COLUMN id INT AUTO_INCREMENT;"))
            conn.execute(text("ALTER TABLE transactions MODIFY COLUMN id INT AUTO_INCREMENT;"))
            conn.execute(text("ALTER TABLE products MODIFY COLUMN image_url TEXT;"))
        print("\nSuccessfully ensured AUTO_INCREMENT and TEXT image_url on products.\n")
    except Exception as e:
        from sqlalchemy import text
        err_msg = f"\nFailed to apply database column alters: {e}\n"
        print(err_msg)
        try:
            with open("debug_log.txt", "w") as f:
                f.write(err_msg)
        except Exception:
            pass
    
    # Write structural schema details to debug_log.txt for review
    try:
        log_lines = []
        log_lines.append("DATABASE STRUCTURE:")
        
        with engine.connect() as conn:
            for table in ["vendors", "products", "transactions"]:
                log_lines.append(f"\nTable DESCRIBE: {table}")
                try:
                    rows = conn.execute(text(f"DESCRIBE {table}")).fetchall()
                    for row in rows:
                        log_lines.append(f" - {row[0]}: {row[1]} (Null={row[2]}, Key={row[3]}, Default={row[4]}, Extra={row[5]})")
                except Exception as tbl_err:
                    log_lines.append(f"Failed to describe {table}: {tbl_err}")
                
        with open("debug_log.txt", "w") as f:
            f.write("\n".join(log_lines))
        print("\nSuccessfully wrote database table structure to debug_log.txt\n")
    except Exception as e:
        print(f"\nFailed to inspect database schema: {e}\n")

# -------------------------------------------------------------
# Routes - Login
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def get_login(
    request: Request
):
    return templates.TemplateResponse(request, "login.html", {"role": "vendor", "error": None})

@app.post("/login")
def post_login(
    response: Response,
    request: Request,
    role: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    email = email.strip()
    
    if role == "admin":
        # Authenticate Admin
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            # Success: redirect to Admin Dashboard
            redirect = RedirectResponse(url="/admin/dashboard", status_code=303)
            redirect.set_cookie(key="admin_session", value=ADMIN_SESSION_VAL, httponly=True, max_age=3600, path="/")
            redirect.delete_cookie(key="vendor_session", path="/")
            return redirect
        else:
            # Fail: return error
            error_msg = "Invalid admin email or password. Please try again."
            return templates.TemplateResponse(
                request,
                "login.html", 
                {"role": "admin", "email": "", "error": error_msg}
            )
            
    elif role == "vendor":
        # Authenticate Vendor
        try:
            vendor = db.query(models.Vendor).filter(models.Vendor.email == email).first()
        except Exception as e:
            print(f"Database error during vendor login: {e}")
            error_msg = "A server or database error occurred. Please try again later."
            return templates.TemplateResponse(
                request,
                "login.html", 
                {"role": "vendor", "email": "", "error": error_msg}
            )
            
        if not vendor or not verify_password(password, vendor.password_hash):
            error_msg = "Invalid email or password."
            return templates.TemplateResponse(
                request,
                "login.html", 
                {"role": "vendor", "email": "", "error": error_msg}
            )
        
        # Check Account Approval Status
        if vendor.status == "Pending":
            error_msg = "Your vendor account is pending admin approval."
            return templates.TemplateResponse(
                request,
                "login.html", 
                {"role": "vendor", "email": "", "error": error_msg}
            )
        elif vendor.status == "Suspended":
            error_msg = "Your vendor account has been suspended. Please contact admin."
            return templates.TemplateResponse(
                request,
                "login.html", 
                {"role": "vendor", "email": "", "error": error_msg}
            )
        elif vendor.status == "Approved":
            # Success: redirect to Vendor Dashboard
            redirect = RedirectResponse(url="/vendor/dashboard", status_code=303)
            redirect.set_cookie(key="vendor_session", value=vendor.email, httponly=True, max_age=3600, path="/")
            redirect.delete_cookie(key="admin_session", path="/")
            return redirect

    error_msg = "Invalid role selected."
    return templates.TemplateResponse(request, "login.html", {"role": "vendor", "error": error_msg})

# -------------------------------------------------------------
# Routes - Register
# -------------------------------------------------------------
@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse(request, "register.html", {"error": None})

@app.post("/register")
def post_register(
    request: Request,
    full_name: str = Form(...),
    business_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone_number: str = Form(None),
    business_address: str = Form(None),
    db: Session = Depends(get_db)
):
    full_name = full_name.strip()
    business_name = business_name.strip()
    email = email.strip()
    
    # 1. Validation
    if not full_name or not business_name or not email or not password:
        return templates.TemplateResponse(
            request,
            "register.html", 
            {"error": "Registration was not successful. Please fill in all required (*) fields.", "full_name": full_name, "business_name": business_name, "email": email, "phone_number": phone_number, "business_address": business_address}
        )
        
    if len(password) < 6:
        return templates.TemplateResponse(
            request,
            "register.html", 
            {"error": "Registration was not successful. Password must be at least 6 characters.", "full_name": full_name, "business_name": business_name, "email": email, "phone_number": phone_number, "business_address": business_address}
        )

    # 2. Check duplicate email
    existing_vendor = db.query(models.Vendor).filter(models.Vendor.email == email).first()
    if existing_vendor:
        return templates.TemplateResponse(
            request,
            "register.html", 
            {"error": "Registration was not successful. Email is already registered.", "full_name": full_name, "business_name": business_name, "email": email, "phone_number": phone_number, "business_address": business_address}
        )

    # 3. Create Vendor in Pending Status
    new_vendor = models.Vendor(
        full_name=full_name,
        business_name=business_name,
        email=email,
        password_hash=hash_password(password),
        phone_number=phone_number,
        business_address=business_address,
        status="Pending"
    )
    
    try:
        db.add(new_vendor)
        db.commit()
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "register.html", 
            {"error": "Registration was not successful. A database error occurred. Please try again later.", "full_name": full_name, "business_name": business_name, "email": email, "phone_number": phone_number, "business_address": business_address}
        )

    # 4. Render registration page with success context (do not redirect)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"success": True, "error": None}
    )

@app.get("/confirmation", response_class=HTMLResponse)
def get_confirmation(request: Request):
    return templates.TemplateResponse(request, "confirmation.html", {})

# -------------------------------------------------------------
# Routes - Admin Dashboard
# -------------------------------------------------------------
@app.get("/admin/dashboard", response_class=HTMLResponse)
def get_admin_dashboard(
    request: Request,
    admin_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    # Verify Admin Session
    if admin_session != ADMIN_SESSION_VAL:
        return RedirectResponse(url="/login", status_code=303)

    # Fetch Platform Metrics
    total_vendors = db.query(models.Vendor).count()
    pending_vendors = db.query(models.Vendor).filter(models.Vendor.status == "Pending").count()
    approved_vendors = db.query(models.Vendor).filter(models.Vendor.status == "Approved").count()
    suspended_vendors = db.query(models.Vendor).filter(models.Vendor.status == "Suspended").count()

    stats = {
        "total": total_vendors,
        "pending": pending_vendors,
        "approved": approved_vendors,
        "suspended": suspended_vendors
    }

    # Fetch All Recent Vendors (no limit)
    recent_vendors = db.query(models.Vendor).order_by(models.Vendor.email.desc()).all()

    # Fetch All Vendors for Vendor Management
    all_vendors = db.query(models.Vendor).order_by(models.Vendor.email.desc()).all()

    return templates.TemplateResponse(
        request,
        "dashboard.html", 
        {
            "stats": stats, 
            "recent_vendors": recent_vendors, 
            "all_vendors": all_vendors
        }
    )

# -------------------------------------------------------------
# Admin Action APIs
# -------------------------------------------------------------
@app.post("/admin/vendors/{email}/approve")
def approve_vendor(
    email: str,
    admin_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if admin_session != ADMIN_SESSION_VAL:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    vendor = db.query(models.Vendor).filter(models.Vendor.email == email).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    vendor.status = "Approved"
    db.commit()
    return {"message": "Vendor approved successfully."}

@app.post("/admin/vendors/{email}/suspend")
def suspend_vendor(
    email: str,
    admin_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if admin_session != ADMIN_SESSION_VAL:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    vendor = db.query(models.Vendor).filter(models.Vendor.email == email).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
        
    vendor.status = "Suspended"
    db.commit()
    return {"message": "Vendor suspended successfully."}

# -------------------------------------------------------------
# Routes - Vendor Dashboard
# -------------------------------------------------------------
@app.get("/vendor/dashboard", response_class=HTMLResponse)
def get_vendor_dashboard(
    request: Request,
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        return RedirectResponse(url="/login", status_code=303)
        
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor:
        redirect = RedirectResponse(url="/login", status_code=303)
        redirect.delete_cookie(key="vendor_session", path="/")
        return redirect

    if vendor.status != "Approved":
        redirect = RedirectResponse(url="/login", status_code=303)
        redirect.delete_cookie(key="vendor_session", path="/")
        return redirect

    # 1. Fetch products listed count
    products_count = db.query(models.Product).filter(models.Product.vendor_email == vendor.email).count()

    # 2. Fetch sales, transactions, and revenue metrics
    from sqlalchemy import func
    sales_data = db.query(
        func.sum(models.Transaction.quantity).label("total_sales"),
        func.sum(models.Transaction.amount).label("total_revenue"),
        func.count(models.Transaction.id).label("total_transactions")
    ).filter(models.Transaction.vendor_email == vendor.email).first()

    total_sales = int(sales_data.total_sales or 0)
    total_revenue = float(sales_data.total_revenue or 0.0)
    total_transactions = int(sales_data.total_transactions or 0)

    metrics = {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "products_listed": products_count
    }

    # 3. Fetch products
    recent_products = db.query(models.Product).filter(models.Product.vendor_email == vendor.email).order_by(models.Product.id.desc()).limit(5).all()
    all_products = db.query(models.Product).filter(models.Product.vendor_email == vendor.email).order_by(models.Product.id.desc()).all()

    return templates.TemplateResponse(
        request, 
        "vendor_dashboard.html", 
        {
            "vendor": vendor, 
            "metrics": metrics,
            "recent_products": recent_products,
            "all_products": all_products
        }
    )

@app.post("/vendor/products/add")
def post_add_product(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(None),
    description: str = Form(None),
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        return RedirectResponse(url="/login", status_code=303)
        
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        return RedirectResponse(url="/login", status_code=303)

    # Clean description
    if not description:
        description = f"A premium {name} categorized under {category}. Crafted from top-tier components to deliver style, utility, and reliable performance."
    
    # Clean image url
    if not image_url or not image_url.strip():
        # Clean fallback image
        image_url = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&auto=format&fit=crop&q=60"

    new_product = models.Product(
        name=name.strip(),
        category=category.strip(),
        price=price,
        stock=stock,
        image_url=image_url.strip(),
        description=description.strip(),
        vendor_email=vendor.email
    )

    try:
        db.add(new_product)
        db.commit()
    except Exception as e:
        db.rollback()
        import traceback
        err_msg = f"\n\nPRODUCT INSERTION ERROR:\n{e}\n{traceback.format_exc()}\n"
        print(err_msg)
        try:
            with open("debug_log.txt", "a") as f:
                f.write(err_msg)
        except Exception as log_err:
            print(f"Failed to write to debug_log.txt: {log_err}")
        raise HTTPException(status_code=500, detail="Database insertion error. Please try again later.")

    # Redirect to catalog view hash with status
    return RedirectResponse(url="/vendor/dashboard?status=added#my-catalog-view", status_code=303)

@app.post("/vendor/profile/update")
def update_vendor_profile(
    request: Request,
    full_name: str = Form(...),
    business_name: str = Form(...),
    phone_number: str = Form(None),
    business_address: str = Form(None),
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    vendor.full_name = full_name.strip()
    vendor.business_name = business_name.strip()
    vendor.phone_number = phone_number.strip() if phone_number else None
    vendor.business_address = business_address.strip() if business_address else None
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")
        
    return {"message": "Profile updated successfully."}

@app.get("/vendor/product/{product_id}")
def get_vendor_product(
    product_id: int,
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.vendor_email == vendor.email
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "stock": product.stock,
        "image_url": product.image_url,
        "description": product.description
    }

@app.post("/vendor/products/edit/{product_id}")
def edit_vendor_product(
    product_id: int,
    name: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    image_url: str = Form(None),
    description: str = Form(None),
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        return RedirectResponse(url="/login", status_code=303)
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        return RedirectResponse(url="/login", status_code=303)
        
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.vendor_email == vendor.email
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product.name = name.strip()
    product.category = category.strip()
    product.price = price
    product.stock = stock
    product.image_url = image_url.strip() if image_url else "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&auto=format&fit=crop&q=60"
    product.description = description.strip() if description else f"A premium {name} categorized under {category}."
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database update failed")
        
    # Redirect to catalog with updated status
    return RedirectResponse(url="/vendor/dashboard?status=updated#my-catalog-view", status_code=303)

@app.post("/vendor/products/delete/{product_id}")
def delete_vendor_product(
    product_id: int,
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.vendor_email == vendor.email
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    try:
        db.delete(product)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database deletion failed")
        
    return {"message": "Product deleted successfully."}

@app.post("/vendor/profile/change-password")
def change_vendor_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    vendor_session: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not vendor_session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_session).first()
    if not vendor or vendor.status != "Approved":
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    # Validation
    # 1. Verify current password
    if not verify_password(current_password, vendor.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
        
    # 2. New password length
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        
    # 3. New password mismatch
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
        
    # 4. New password cannot be same as current password
    if verify_password(new_password, vendor.password_hash):
        raise HTTPException(status_code=400, detail="New password cannot be the same as current password.")
        
    # Update password securely
    vendor.password_hash = hash_password(new_password)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update password in database.")
        
    return {"message": "Password changed successfully!"}

# -------------------------------------------------------------
# Routes - Logout
# -------------------------------------------------------------
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="admin_session", path="/")
    response.delete_cookie(key="vendor_session", path="/")
    return response

@app.get("/debug-db")
def debug_db(db: Session = Depends(get_db)):
    from sqlalchemy import inspect
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns("vendors")
        return {
            "status": "success",
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": str(col["default"]) if col["default"] is not None else None,
                    "primary_key": col.get("primary_key", 0)
                }
                for col in columns
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
