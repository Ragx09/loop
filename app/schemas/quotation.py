from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QuotationItemIn(BaseModel):
    particulars: str = Field(max_length=500)
    hsn_code: str | None = Field(default=None, max_length=32)
    #: Price for a single quantity.
    price: Decimal
    quantity: int = Field(default=1, ge=1)


class QuotationCreate(BaseModel):
    business_id: int
    template_key: str
    customer_name: str = Field(max_length=160)
    customer_address: str | None = Field(default=None, max_length=500)
    quotation_number: str | None = Field(default=None, max_length=60)
    quotation_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    items: list[QuotationItemIn]


class QuotationItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    particulars: str
    hsn_code: str | None
    price: Decimal
    quantity: int
    line_total: Decimal


class QuotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_number: str
    quotation_date: date
    template_key: str
    customer_name: str
    customer_address: str | None
    notes: str | None
    items: list[QuotationItemOut]
    total: Decimal


class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str


class TemplateOut(BaseModel):
    key: str
    name: str
    description: str
