from typing import Optional, List, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum, Numeric, Boolean, DateTime
import uuid
import enum

class DiscountTypeEnum(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"

class SegmentTypeEnum(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"
    DEALER = "DEALER"

class Discount(SQLModel, table=True):
    __tablename__ = "discounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(unique=True, nullable=False)
    description: Optional[str] = None
    type: DiscountTypeEnum = Field(sa_column=Column(Enum(DiscountTypeEnum), nullable=False))
    value: float = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    start_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    end_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))

    rules: List["DiscountRules"] = Relationship(back_populates="discount")

class DiscountRules(SQLModel, table=True):
    __tablename__ = "discount_rules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    discount_id: uuid.UUID = Field(foreign_key="discounts.id", nullable=False)
    segment_type: Optional[SegmentTypeEnum] = Field(default=None, sa_column=Column(Enum(SegmentTypeEnum), nullable=True))
    tenant_id: Optional[str] = Field(default=None, nullable=True)
    priority: int = Field(default=0, nullable=False)

    discount: Discount = Relationship(back_populates="rules")
