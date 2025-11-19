from typing import Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    Item,
    ItemsResponse,
    BusinessCustomer,
    BusinessWithItemsResponse,
)
from utils import fetch_sheet_rows

app = FastAPI(
    title="Google Sheet Shop API",
    description="Reads Google Sheets for customers and items and exposes them as JSON.",
    version="2.0.0",
)

origins = [
    "http://13.233.199.188"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: Replace this with your actual Google Sheet URL for customers
CUSTOMERS_SHEET_LINK = "https://docs.google.com/spreadsheets/d/1TQP-Nt4P3zRHjuFNDdemP_pWQXp4LbazwppD-KKg5Io/edit?gid=0"

# In-memory cache for customers, keyed by ShopUsername
customers_cache: Dict[str, BusinessCustomer] = {}


def parse_bool(value: str) -> bool:
    if value is None:
        return False
    v = value.strip().lower()
    return v in ("true", "1", "yes", "y")


def parse_int(value: str, default: int = 0) -> int:
    if value is None or value.strip() == "":
        return default
    return int(float(value))


def parse_float(value: str, default: float = 0.0) -> float:
    if value is None or value.strip() == "":
        return default
    return float(value)


def parse_tags(value: str):
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


@app.post("/updateCustomers")
def update_customers():
    """
    Fetch customers from the constant Google Sheet and update in-memory cache.

    Expected columns in the sheet (header row):
    BusinessName, BusinessType, Address, MobileNo, Pincode,
    MapLocation, ShopUsername, ConvenienceFee, Description,
    SheetLink, SubscriptionDate
    """
    global customers_cache
    try:
        rows = fetch_sheet_rows(CUSTOMERS_SHEET_LINK)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch customers sheet: {e}")

    new_cache: Dict[str, BusinessCustomer] = {}

    for row in rows:
        business_name = (row.get("BusinessName") or "").strip()
        shop_username = (row.get("ShopUsername") or "").strip()
        sheet_link = (row.get("SheetLink") or "").strip()

        # Skip incomplete rows
        if not business_name or not shop_username or not sheet_link:
            continue

        try:
            customer = BusinessCustomer(
                BusinessName=business_name,
                BusinessType=(row.get("BusinessType") or "").strip(),
                Address=(row.get("Address") or "").strip(),
                MobileNo=(row.get("MobileNo") or "").strip(),
                Pincode=(row.get("Pincode") or "").strip(),
                MapLocation=(row.get("MapLocation") or "").strip(),
                ShopUsername=shop_username,
                ConvenienceFee=parse_float(row.get("ConvenienceFee"), 0.0),
                Description=(row.get("Description") or "").strip(),
                SheetLink=sheet_link,
                SubscriptionDate=(row.get("SubscriptionDate") or "").strip(),
            )
        except Exception as e:
            # Skip any bad row instead of failing everything
            print(f"Skipping customer row due to error: {e}, row={row}")
            continue

        new_cache[shop_username] = customer

    customers_cache = new_cache
    return {"message": "Customers updated 2", "count": len(customers_cache)}


@app.get("/items", response_model=ItemsResponse)
def get_items_from_sheet(sheet_url: str = Query(..., description="Google Sheet URL for items")):
    """
    Original endpoint: directly read an items sheet URL and return items array.
    """
    try:
        rows = fetch_sheet_rows(sheet_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {e}")

    items: List[Item] = []

    for row in rows:
        name = (row.get("Name") or "").strip()
        category = (row.get("Category") or "").strip()
        rate_str = (row.get("Rate") or "").strip()

        # Skip if required values missing
        if name == "" or category == "" or rate_str == "":
            continue

        try:
            item = Item(
                id=parse_int(row.get("id")),
                Name=name,
                Rate=parse_float(rate_str),
                Discount=parse_float(row.get("Discount")),
                combo_quantity=parse_int(row.get("combo_quantity")),
                combo_discount=parse_float(row.get("combo_discount")),
                Category=category,
                Stock=parse_bool(row.get("Stock")),
                tags=parse_tags(row.get("tags")),
                image1=(row.get("image1") or "").strip(),
                image2=(row.get("image2") or "").strip(),
                video=(row.get("video") or "").strip(),
            )
        except Exception as e:
            print(f"Skipping item row due to error: {e}, row={row}")
            continue

        items.append(item)

    return ItemsResponse(items=items)


@app.get("/getitems", response_model=BusinessWithItemsResponse)
def get_items_for_shop(shop_username: str = Query(..., description="ShopUsername of the business")):
    """
    1. Use the in-memory customers_cache (populated via /updateCustomers)
    2. Find the customer by ShopUsername
    3. Use its SheetLink to fetch items
    4. Return business info + Items array in the response
    """
    # Ensure customers_cache is populated
    if not customers_cache:
        # Optionally auto-refresh; for now, require explicit update
        raise HTTPException(status_code=400, detail="Customer cache is empty. Call /updateCustomers first.")

    customer = customers_cache.get(shop_username)
    if not customer:
        raise HTTPException(status_code=404, detail=f"No customer found for ShopUsername '{shop_username}'")

    if not customer.SheetLink:
        raise HTTPException(status_code=400, detail=f"No SheetLink configured for ShopUsername '{shop_username}'")

    # Fetch items using the customer's sheet link
    try:
        rows = fetch_sheet_rows(customer.SheetLink)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch items sheet: {e}")

    items: List[Item] = []

    for row in rows:
        name = (row.get("Name") or "").strip()
        category = (row.get("Category") or "").strip()
        rate_str = (row.get("Rate") or "").strip()

        if name == "" or category == "" or rate_str == "":
            continue

        try:
            item = Item(
                id=parse_int(row.get("id")),
                Name=name,
                Rate=parse_float(rate_str),
                Discount=parse_float(row.get("Discount")),
                combo_quantity=parse_int(row.get("combo_quantity")),
                combo_discount=parse_float(row.get("combo_discount")),
                Category=category,
                Stock=parse_bool(row.get("Stock")),
                tags=parse_tags(row.get("tags")),
                image1=(row.get("image1") or "").strip(),
                image2=(row.get("image2") or "").strip(),
                video=(row.get("video") or "").strip(),
            )
        except Exception as e:
            print(f"Skipping item row due to error: {e}, row={row}")
            continue

        items.append(item)

    # Build response WITHOUT exposing SheetLink / SubscriptionDate
    return BusinessWithItemsResponse(
        BusinessName=customer.BusinessName,
        BusinessType=customer.BusinessType,
        Address=customer.Address,
        MobileNo=customer.MobileNo,
        Pincode=customer.Pincode,
        MapLocation=customer.MapLocation,
        ShopUsername=customer.ShopUsername,
        ConvenienceFee=customer.ConvenienceFee,
        Description=customer.Description or "",
        Items=items,
    )
