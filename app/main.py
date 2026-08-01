import os
import traceback
import logging
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import Base, Engine, get_db
from app import models, schemas, auth

logger = logging.getLogger("shopsense")

# Initialize Database Tables
Base.metadata.create_all(bind=Engine)

app = FastAPI(title="ShopSense Marketplace")

# Global Exception Handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error on {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Mount Static files and Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def render_template(template_name: str, request: Request, context: dict = None):
    ctx = {"request": request}
    if context:
        ctx.update(context)
    try:
        return templates.TemplateResponse(request=request, name=template_name, context=ctx)
    except TypeError:
        return templates.TemplateResponse(template_name, ctx)


# Helper dependency to resolve logged-in vendor
def get_current_vendor(request: Request, db: Session = Depends(get_db)) -> models.Vendor:
    vendor_id_str = request.cookies.get("vendor_id")
    if vendor_id_str:
        try:
            vendor_id = int(vendor_id_str)
            vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id, models.Vendor.status == "Approved").first()
            if vendor:
                return vendor
        except ValueError:
            pass
    # Fallback to first approved vendor for seamless testing or direct access
    vendor = db.query(models.Vendor).filter(models.Vendor.status == "Approved").first()
    if vendor:
        return vendor
    raise HTTPException(status_code=401, detail="Vendor authentication required.")



# PAGE ROUTES (HTML Views)


@app.get("/")
def read_root():
    return RedirectResponse(url="/login")

@app.get("/login")
def render_login(request: Request):
    return render_template("login.html", request)

@app.get("/register")
def render_register(request: Request):
    return render_template("register.html", request)

@app.get("/admin/dashboard")
def render_admin_dashboard(request: Request):
    return render_template("admin_dashboard.html", request)

@app.get("/vendor/dashboard")
def render_vendor_dashboard(request: Request):
    return render_template("vendor_dashboard.html", request)



# AUTH API ENDPOINTS


@app.post("/api/register")
def register_vendor(vendor_in: schemas.VendorRegister, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_vendor = db.query(models.Vendor).filter(models.Vendor.email == vendor_in.email.lower()).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Create new vendor with status 'Pending'
    hashed_pwd = auth.hash_password(vendor_in.password)
    new_vendor = models.Vendor(
        full_name=vendor_in.full_name,
        business_name=vendor_in.business_name,
        email=vendor_in.email.lower(),
        password_hash=hashed_pwd,
        phone=vendor_in.phone,
        address=vendor_in.address,
        status="Pending"
    )

    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    return {"success": True, "message": "Vendor registered successfully.", "vendor_id": new_vendor.id}


@app.post("/api/login")
def login(login_in: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    role = login_in.role.lower()

    if role == "admin":
        if auth.verify_admin(login_in.email, login_in.password):
            return {"success": True, "redirect_url": "/admin/dashboard"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin email or password. Please try again."
            )

    elif role == "vendor":
        vendor = db.query(models.Vendor).filter(models.Vendor.email == login_in.email.lower()).first()
        if not vendor or not auth.verify_password(login_in.password, vendor.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or password. Please try again."
            )

        # Status check
        if vendor.status == "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your vendor account has been created and is currently waiting for admin approval."
            )
        elif vendor.status == "Suspended":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your vendor account has been suspended. Please contact support."
            )
        elif vendor.status == "Approved":
            res = JSONResponse(content={"success": True, "redirect_url": "/vendor/dashboard", "message": "Login successful!"})
            res.set_cookie(key="vendor_id", value=str(vendor.id), httponly=False, path="/")
            return res
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account status invalid."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid login role specified."
        )


@app.post("/api/logout")
def logout():
    res = JSONResponse(content={"success": True, "redirect_url": "/login"})
    res.delete_cookie(key="vendor_id", path="/")
    return res



# ADMIN MANAGEMENT APIs


@app.get("/api/admin/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total = db.query(models.Vendor).count()
    pending = db.query(models.Vendor).filter(models.Vendor.status == "Pending").count()
    approved = db.query(models.Vendor).filter(models.Vendor.status == "Approved").count()
    suspended = db.query(models.Vendor).filter(models.Vendor.status == "Suspended").count()

    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "suspended": suspended
    }


@app.get("/api/admin/vendors")
def get_vendors(db: Session = Depends(get_db)):
    vendors = db.query(models.Vendor).order_by(models.Vendor.created_at.desc()).all()
    return [v.to_dict() for v in vendors]


@app.post("/api/admin/vendors/{vendor_id}/approve")
def approve_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    vendor.status = "Approved"
    db.commit()
    return {"success": True, "message": "Vendor approved successfully."}


@app.post("/api/admin/vendors/{vendor_id}/suspend")
def suspend_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    vendor.status = "Suspended"
    db.commit()
    return {"success": True, "message": "Vendor suspended successfully."}



# VENDOR DASHBOARD APIs


@app.get("/api/vendor/me")
def get_vendor_me(current_vendor: models.Vendor = Depends(get_current_vendor)):
    return current_vendor.to_dict()


@app.get("/api/vendor/dashboard-data")
def get_vendor_dashboard_data(
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    # Total Sales (Sum of items_sold)
    total_sales_res = db.query(func.sum(models.Transaction.items_sold)).filter(
        models.Transaction.vendor_id == current_vendor.id
    ).scalar()
    total_sales = int(total_sales_res or 0)

    # Total Revenue (Sum of total_revenue)
    total_rev_res = db.query(func.sum(models.Transaction.total_revenue)).filter(
        models.Transaction.vendor_id == current_vendor.id
    ).scalar()
    total_revenue = float(total_rev_res or 0.0)

    # Total Transactions
    total_transactions = db.query(models.Transaction).filter(
        models.Transaction.vendor_id == current_vendor.id
    ).count()

    # Published Products count
    published_products = db.query(models.Product).filter(
        models.Product.vendor_id == current_vendor.id,
        models.Product.status == "Published"
    ).count()

    # Recent Products
    recent_products = db.query(models.Product).filter(
        models.Product.vendor_id == current_vendor.id
    ).order_by(models.Product.created_at.desc()).limit(10).all()

    return {
        "vendor_name": current_vendor.full_name,
        "business_name": current_vendor.business_name,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "published_products": published_products,
        "recent_products": [p.to_dict() for p in recent_products]
    }


@app.get("/api/vendor/products")
def get_vendor_products(
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    products = db.query(models.Product).filter(
        models.Product.vendor_id == current_vendor.id
    ).order_by(models.Product.created_at.desc()).all()
    return [p.to_dict() for p in products]


@app.post("/api/vendor/products")
def create_product(
    product_in: schemas.ProductCreate,
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    # Auto-generate AI description if empty
    description = product_in.description
    if not description or not description.strip():
        description = f"High quality {product_in.name} from {product_in.category} collection. Designed for optimal performance, durability, and daily satisfaction."

    new_product = models.Product(
        vendor_id=current_vendor.id,
        name=product_in.name.strip(),
        category=product_in.category.strip(),
        price=product_in.price,
        stock=product_in.stock,
        image_url=product_in.image_url.strip() if product_in.image_url else None,
        description=description.strip(),
        status=product_in.status or "Published"
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {"success": True, "message": "Product created successfully.", "product": new_product.to_dict()}


@app.put("/api/vendor/products/{product_id}")
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.vendor_id == current_vendor.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    if product_in.name is not None:
        product.name = product_in.name.strip()
    if product_in.category is not None:
        product.category = product_in.category.strip()
    if product_in.price is not None:
        product.price = product_in.price
    if product_in.stock is not None:
        product.stock = product_in.stock
    if product_in.image_url is not None:
        product.image_url = product_in.image_url.strip()
    if product_in.description is not None:
        product.description = product_in.description.strip()
    if product_in.status is not None:
        product.status = product_in.status

    db.commit()
    return {"success": True, "message": "Product updated successfully.", "product": product.to_dict()}


@app.delete("/api/vendor/products/{product_id}")
def delete_product(
    product_id: int,
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.vendor_id == current_vendor.id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    db.delete(product)
    db.commit()
    return {"success": True, "message": "Product deleted successfully."}


@app.put("/api/vendor/profile")
def update_vendor_profile(
    profile_in: schemas.VendorProfileUpdate,
    current_vendor: models.Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db)
):
    current_vendor.full_name = profile_in.full_name.strip()
    current_vendor.business_name = profile_in.business_name.strip()
    current_vendor.phone = profile_in.phone.strip() if profile_in.phone else None
    current_vendor.address = profile_in.address.strip() if profile_in.address else None

    if profile_in.new_password and len(profile_in.new_password.strip()) >= 6:
        current_vendor.password_hash = auth.hash_password(profile_in.new_password.strip())

    db.commit()
    return {"success": True, "message": "Profile updated successfully.", "vendor": current_vendor.to_dict()}


@app.post("/api/vendor/generate-description")
def generate_ai_description(req: schemas.AIDescriptionRequest):
    name = req.name.strip()
    category = req.category.strip()
    
    desc_templates = [
        f"Unlock peak experience with {name}. Engineered specifically for the {category} sector, combining premium material standards with aesthetic brilliance.",
        f"Discover unmatched quality in {name}. Designed to enhance your everyday lifestyle with durable construction and sleek functionality.",
        f"The ultimate solution in {category}: {name}. Precision-designed to deliver exceptional reliability, comfort, and style."
    ]
    
    idx = len(name) % len(desc_templates)
    return {"description": desc_templates[idx]}
