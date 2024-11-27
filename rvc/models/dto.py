from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime    

class OrderDetail_InputDTO(BaseModel):
    quantity : int = Field(..., description="Quantity per product")
    totalDetailOrderValue: float = Field(..., description="Total Order value")
    totalDetailOrderUnTaxed: float = Field(..., description="Total Order value")
    courseDate: Optional[datetime] = Field(default=None, description="Course date")
    sku: int = Field(..., description="product identifier")

class DigitalCard_InputDTO(BaseModel):
    name: str = Field(..., description="Cardholder's name")
    email: str = Field(..., description="Cardholder's email")
    phone: str = Field(..., description="Cardholder's phone number")
    service: str = Field(..., description="Service offered")
    city: str = Field(..., description="Cardholder's city")
    address: str = Field(..., description="Cardholder's address")
    website: Optional[str] = Field(None, description="Cardholder's website")
    facebook: Optional[str] = Field(None, description="Facebook profile")
    instagram: Optional[str] = Field(None, description="Instagram profile")

class Order_InputDTO(BaseModel):
    nit: str = Field(..., description="Customer Company nit")
    buyerEmail: str = Field(..., description="Customer company mail")
    totalOrderValue: float = Field(..., description="Total Order value")
    totalOrderUnTaxed: float = Field(..., description="Order value before taxes")
    detailsOrder: List[OrderDetail_InputDTO] = Field(default=[], description="Order detail")
    orderId: str = Field(..., description="Purchase order number")
    salesmanEmail: str = Field(..., description="Salesman email")
    sponsor: Optional[str] = Field(default=None, description="RVC program nit sponsor")
    digitalCards: Optional[List[DigitalCard_InputDTO]] = Field(
        default=[], description="Digital cards data"
    )
    origin: str = Field(..., description="Order origin")
    cellphone: Optional[str] = Field(
        default=None, description="Buyer Cellphone when origin is WhatsApp"
    )
    isSeller: Optional[bool] = Field(
        default=False, description="Indicate if buyer is seller"
    )
