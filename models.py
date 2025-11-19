from typing import List, Optional
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    Name: str
    Rate: float
    Discount: float
    combo_quantity: int
    combo_discount: float
    Category: str
    Stock: bool
    tags: List[str]
    image1: Optional[str] = ""
    image2: Optional[str] = ""
    video: Optional[str] = ""


class ItemsResponse(BaseModel):
    items: List[Item]


class BusinessCustomer(BaseModel):
    BusinessName: str
    BusinessType: str
    Address: str
    MobileNo: str
    Pincode: str
    MapLocation: str
    ShopUsername: str
    ConvenienceFee: float
    Description: Optional[str] = ""
    SheetLink: Optional[str] = ""
    SubscriptionDate: Optional[str] = ""


class BusinessWithItemsResponse(BaseModel):
    BusinessName: str
    BusinessType: str
    Address: str
    MobileNo: str
    Pincode: str
    MapLocation: str
    ShopUsername: str
    ConvenienceFee: float
    Description: Optional[str] = ""
    Items: List[Item]
