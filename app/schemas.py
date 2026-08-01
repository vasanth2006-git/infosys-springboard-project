from typing import Optional
from pydantic import BaseModel, Field

try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str

class VendorRegister(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full Name is required")
    business_name: str = Field(..., min_length=1, description="Business Name is required")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", description="Valid Email Address is required")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    phone: Optional[str] = None
    address: Optional[str] = None

class LoginRequest(BaseModel):
    email: str = Field(..., description="Email Address")
    password: str = Field(..., description="Password")
    role: str = Field(..., description="Role: 'vendor' or 'admin'")

class StatusUpdate(BaseModel):
    status: str = Field(..., description="New status: 'Approved' or 'Suspended'")

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Product Name is required")
    category: str = Field(..., min_length=1, description="Category is required")
    price: float = Field(..., ge=0, description="Price must be non-negative")
    stock: int = Field(..., ge=0, description="Stock must be non-negative integer")
    image_url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "Published"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class VendorProfileUpdate(BaseModel):
    full_name: str
    business_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    new_password: Optional[str] = None

class AIDescriptionRequest(BaseModel):
    name: str
    category: str


