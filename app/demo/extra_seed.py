"""Sample data for the customer, inventory and invoicing modules.

Kept beside app/demo/seed.py rather than inside it so the original task and
quotation seed stays readable. Everything here is invented.
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.enums import PaymentMethod
from app.models.customer import Customer, Equipment
from app.models.inventory import InventoryItem, MaterialUsed
from app.models.invoice import Invoice, InvoiceItem, Payment
from app.models.service_report import ServiceReport
from app.models.task import Task
from app.models.user import User
from app.services.invoice_service import InvoiceService

# Matches the customer names already used by the task and quotation seed, so
# the history panel on each customer is populated rather than empty.
CUSTOMERS: tuple[dict, ...] = (
    {
        "name": "Sunrise Textiles",
        "phone": "+91 98400 11223",
        "email": "works@sunrisetextiles.example",
        "address": "Plot 14, Industrial Estate, Coimbatore 641021",
        "gstin": "33AABCS1429B1ZQ",
        "equipment": [
            ("Screw Compressor", "CX-220", "CX220-8841", -900),
            ("Air Dryer", "AD-40", "AD40-2213", -540),
        ],
    },
    {
        "name": "Meridian Packaging",
        "phone": "+91 98401 55447",
        "email": "maintenance@meridianpack.example",
        "address": "62 GIDC Phase II, Vapi 396195",
        "gstin": "24AAECM7781H1Z5",
        "equipment": [("Sealing Machine", "SH-9", "SH9-1190", -1200)],
    },
    {
        "name": "Everest Plastics",
        "phone": "+91 98402 77881",
        "email": "plant@everestplastics.example",
        "address": "24 SIDCO Nagar, Hosur 635109",
        "gstin": "29AAFCE9902K1ZR",
        "equipment": [("Injection Moulding Unit", "IP-75", "IP75-4402", -1600)],
    },
    {
        "name": "Deccan Paper Mills",
        "phone": "+91 98403 22119",
        "email": "engineering@deccanpaper.example",
        "address": "Survey 82/3, Mill Road, Erode 638002",
        "gstin": "33AADCD5517F1ZW",
        "equipment": [("Roller Drive", "DR-30", "DR30-7781", -420)],
    },
    {
        "name": "Kaveri Cold Storage",
        "phone": "+91 98404 66332",
        "email": "ops@kavericold.example",
        "address": "NH-44 Bypass, Krishnagiri 635001",
        "gstin": "33AAGCK3390M1ZT",
        "equipment": [("Condenser Unit", "KC-4", "KC4-5518", -2100)],
    },
    {
        "name": "Nandi Engineering Works",
        "phone": "+91 98405 90014",
        "email": "stores@nandiengg.example",
        "address": "Plot 7, Peenya Industrial Area, Bengaluru 560058",
        "gstin": "29AAJCN1174P1ZL",
        "equipment": [("Gearbox Assembly", "NG-12", "NG12-3306", -760)],
    },
    {
        "name": "Pioneer Rubber",
        "phone": "+91 98406 31278",
        "email": "works@pioneerrubber.example",
        "address": "18 Industrial Road, Ranipet 632403",
        "gstin": "33AACCP8821J1ZB",
        "equipment": [("Rubber Mixer", "PR-500", "PR500-9987", -3000)],
    },
    {
        "name": "Coastal Foods",
        "phone": "+91 98407 45590",
        "email": "plant@coastalfoods.example",
        "address": "Harbour Road, Tuticorin 628004",
        "gstin": "33AAECC4432N1ZY",
        "equipment": [("Blast Chiller", "CF-18", "CF18-2240", -1100)],
    },
)

INVENTORY: tuple[dict, ...] = (
    ("BRG-6204", "Ball Bearing 6204 ZZ", "Bearings", "8482", "180.00", "310.00", 48, 10),
    ("BRG-6206", "Ball Bearing 6206 ZZ", "Bearings", "8482", "245.00", "420.00", 6, 10),
    ("BLT-B72", "V-Belt B72", "Belts", "4010", "390.00", "640.00", 24, 8),
    ("FLT-CX22", "Air Filter Cartridge CX", "Filters", "8421", "1450.00", "2450.00", 15, 5),
    ("SEL-OS35", "Oil Seal 35x52x7", "Seals", "4016", "95.00", "175.00", 60, 15),
    ("HTR-BND1", "Heater Band 1.5 kW", "Heating", "8516", "1180.00", "1950.00", 4, 6),
    ("CTR-PID1", "PID Temperature Controller", "Controls", "9032", "3800.00", "6400.00", 9, 3),
    ("THC-K1M", "Thermocouple K-Type 1m", "Controls", "9025", "520.00", "890.00", 30, 10),
    ("VFD-75K", "VFD 7.5 kW", "Drives", "8504", "24500.00", "38900.00", 3, 2),
    ("CNT-40A", "Contactor 40A", "Switchgear", "8536", "760.00", "1240.00", 18, 6),
)

# Invoices for a believable ledger: one paid, one part-paid, one overdue, one new.
INVOICES: tuple[dict, ...] = (
    {
        "customer": "Sunrise Textiles",
        "business_key": "arcot_enterprises",
        "days_ago": 38,
        "due_in": 15,
        "items": [
            ("Air filter cartridge, CX series", "8421", "2450.00", 2, "18"),
            ("Drive belt, B-section", "4010", "1180.00", 1, "18"),
            ("On-site fitting and trial run", "9987", "3500.00", 1, "18"),
        ],
        "payments": [("full", PaymentMethod.BANK_TRANSFER, 30)],
    },
    {
        "customer": "Deccan Paper Mills",
        "business_key": "arcot_automations",
        "days_ago": 20,
        "due_in": 30,
        "items": [
            ("VFD 7.5 kW with enclosure", "8504", "38900.00", 1, "18"),
            ("Control panel wiring and terminations", "8537", "9750.00", 1, "18"),
        ],
        "payments": [("25000.00", PaymentMethod.UPI, 8)],
    },
    {
        "customer": "Everest Plastics",
        "business_key": "arcot_automations",
        "days_ago": 62,
        "due_in": 15,
        "items": [
            ("Temperature controller, PID", "9032", "6400.00", 3, "18"),
            ("Thermocouple, K-type, 1m", "9025", "890.00", 3, "18"),
        ],
        "payments": [],
    },
    {
        "customer": "Kaveri Cold Storage",
        "business_key": "arcot_enterprises",
        "days_ago": 4,
        "due_in": 30,
        "items": [
            ("Condenser servicing labour", "9987", "4800.00", 1, "18"),
            ("Oil seal 35x52x7", "4016", "175.00", 4, "18"),
        ],
        "payments": [],
    },
)

# Parts consumed on the jobs that were already completed by the task seed.
MATERIALS: tuple[tuple[str, str, int], ...] = (
    ("Sunrise Textiles", "BLT-B72", 1),
    ("Everest Plastics", "HTR-BND1", 1),
    ("Everest Plastics", "CNT-40A", 1),
    ("Meridian Packaging", "SEL-OS35", 2),
)

REPORTS: dict[str, tuple[str, str]] = {
    "Sunrise Textiles": (
        "Inspected the drive assembly, found the belt glazed and slipping under "
        "load. Replaced with a new B-section belt and re-tensioned. Ran the unit "
        "for 30 minutes at full load; no slip, temperature normal.",
        "T. Ramesh",
    ),
    "Meridian Packaging": (
        "Delivered two spare sealing blades and a pair of oil seals to the stores "
        "desk. Stock acknowledged by the shift in-charge.",
        "S. Balaji",
    ),
    "Everest Plastics": (
        "Traced intermittent heating to a failed heater band on zone 2. Replaced "
        "the band and the feed contactor. Temperature now holding within 2 degrees "
        "of setpoint across a full cycle.",
        "K. Prakash",
    ),
}


def reset_extra(db: Session) -> None:
    """Remove the rows this module creates, in foreign-key order."""
    db.execute(delete(Payment))
    db.execute(delete(InvoiceItem))
    db.execute(delete(Invoice))
    db.execute(delete(ServiceReport))
    db.execute(delete(MaterialUsed))
    db.execute(delete(InventoryItem))
    db.execute(delete(Equipment))
    db.execute(delete(Customer))
    db.commit()


def seed_extra(db: Session, proprietor: User) -> dict:
    """Populate customers, equipment, inventory, invoices, payments and reports."""
    customers = _seed_customers(db)
    items = _seed_inventory(db)
    _link_tasks(db, customers)
    materials = _seed_materials(db, items)
    reports = _seed_reports(db, proprietor)
    invoices = _seed_invoices(db, proprietor, customers)

    return {
        "customers": len(customers),
        "inventory": len(items),
        "invoices": invoices,
        "materials": materials,
        "reports": reports,
    }


def _seed_customers(db: Session) -> dict[str, Customer]:
    today = date.today()
    created: dict[str, Customer] = {}

    for spec in CUSTOMERS:
        customer = Customer(
            name=spec["name"],
            phone=spec["phone"],
            email=spec["email"],
            address=spec["address"],
            gstin=spec["gstin"],
            is_active=True,
        )
        db.add(customer)
        db.flush()

        for name, model, serial, day_offset in spec["equipment"]:
            db.add(
                Equipment(
                    customer_id=customer.id,
                    name=name,
                    model=model,
                    serial_number=serial,
                    installed_at=today + timedelta(days=day_offset),
                )
            )
        created[customer.name] = customer

    db.commit()
    return created


def _seed_inventory(db: Session) -> dict[str, InventoryItem]:
    created: dict[str, InventoryItem] = {}
    for sku, name, category, hsn, purchase, selling, qty, minimum in INVENTORY:
        item = InventoryItem(
            sku=sku,
            name=name,
            category=category,
            hsn_code=hsn,
            purchase_price=Decimal(purchase),
            selling_price=Decimal(selling),
            stock_qty=qty,
            min_stock=minimum,
            is_active=True,
        )
        db.add(item)
        created[sku] = item
    db.commit()
    return created


def _link_tasks(db: Session, customers: dict[str, Customer]) -> None:
    """Attach the seeded tasks to their customer records.

    The tasks keep their free-text customer_name; this only fills in the new
    optional link so the customer history panel has something to show.
    """
    for task in db.execute(select(Task)).unique().scalars():
        customer = customers.get(task.customer_name or "")
        if customer is None:
            continue
        task.customer_id = customer.id
        if customer.equipment:
            task.equipment_id = customer.equipment[0].id
    db.commit()


def _seed_materials(db: Session, items: dict[str, InventoryItem]) -> int:
    count = 0
    for customer_name, sku, qty in MATERIALS:
        task = _completed_task_for(db, customer_name)
        item = items.get(sku)
        if task is None or item is None:
            continue
        db.add(MaterialUsed(task_id=task.id, inventory_item_id=item.id, quantity=qty))
        item.stock_qty = max(0, item.stock_qty - qty)
        count += 1
    db.commit()
    return count


def _seed_reports(db: Session, proprietor: User) -> int:
    count = 0
    for customer_name, (work, signature) in REPORTS.items():
        task = _completed_task_for(db, customer_name)
        if task is None or task.report is not None:
            continue
        db.add(
            ServiceReport(
                task_id=task.id,
                work_performed=work,
                meter_reading=task.meter_reading,
                customer_signature=signature,
                created_by_id=task.assigned_engineer_id or proprietor.id,
            )
        )
        count += 1
    db.commit()
    return count


def _seed_invoices(db: Session, proprietor: User, customers: dict[str, Customer]) -> int:
    from app.repositories.business_repository import BusinessRepository

    service = InvoiceService(db)
    businesses = {b.key: b for b in BusinessRepository(db).list_active()}
    today = date.today()
    count = 0

    for spec in INVOICES:
        customer = customers.get(spec["customer"])
        business = businesses.get(spec["business_key"])
        if customer is None or business is None:
            continue

        issued = today - timedelta(days=spec["days_ago"])
        invoice = service.create_invoice(
            proprietor,
            business_id=business.id,
            customer_id=customer.id,
            invoice_date=issued,
            due_date=issued + timedelta(days=spec["due_in"]),
            items=[
                {
                    "particulars": particulars,
                    "hsn_code": hsn,
                    "price": price,
                    "quantity": qty,
                    "tax_rate": rate,
                }
                for particulars, hsn, price, qty, rate in spec["items"]
            ],
        )

        for amount, method, days_ago in spec["payments"]:
            value = invoice.balance_due if amount == "full" else Decimal(amount)
            service.record_payment(
                proprietor,
                invoice.id,
                amount=value,
                method=method,
                paid_at=today - timedelta(days=days_ago),
                reference=f"REF{invoice.id:04d}",
            )

        count += 1

    return count


def _completed_task_for(db: Session, customer_name: str) -> Task | None:
    from app.domain.enums import TaskStatus

    stmt = (
        select(Task)
        .where(Task.customer_name == customer_name)
        .where(Task.status == TaskStatus.COMPLETED)
    )
    return db.execute(stmt).unique().scalars().first()
