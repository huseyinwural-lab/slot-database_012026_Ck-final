from enum import Enum
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"

class Discount(SQLModel, table=True):
    __tablename__ = "discounts"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    code: str = Field(unique=True)
    type: DiscountType
    value: Decimal
    start_at: datetime
    end_at: Optional[datetime] = None
    is_active: bool = True
    
    rules: List["DiscountRule"] = Relationship(back_populates="discount")

class DiscountRule(SQLModel, table=True):
    __tablename__ = "discount_rules"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    discount_id: str = Field(foreign_key="discounts.id")
    segment_type: Optional[str] = None # Enum matches User.segment_type
    tenant_id: Optional[str] = None
    priority: int = 0
    
    discount: Optional[Discount] = Relationship(back_populates="rules")
