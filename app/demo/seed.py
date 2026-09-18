"""Builds the sample data the public demo runs on.

Everything here is invented. The demo deployment uses its own database, so no
real customer, task or quotation ever reaches it.

The seed goes through the ordinary services rather than writing rows directly:
quotation numbering, task workflow rules and password hashing are therefore
exercised exactly as they are in the running application, and cannot drift.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.errors import ValidationError
from app.demo.accounts import DEMO_ACCOUNTS, DEMO_EXTRA_ENGINEERS
from app.domain.enums import TaskStatus, TaskType, UserRole
from app.models.quotation import Quotation, QuotationItem
from app.models.task import Task
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.quotation_service import QuotationService
from app.services.task_service import TaskService


@dataclass(frozen=True)
class SeedSummary:
    """What the seed created, so the CLI and the tests can both check it."""

    users: int
    tasks: int
    quotations: int


@dataclass(frozen=True)
class _TaskSpec:
    task_type: TaskType
    customer_name: str
    model: str
    #: Days from today. Negative is in the past, 0 is today.
    day_offset: int
    #: Status the task should end up in; reached through real transitions.
    status: TaskStatus
    #: Username of the engineer this job belongs to, or None to leave it
    #: unassigned. Named rather than indexed so the data below reads as it
    #: behaves, whatever order the engineers come back in.
    engineer: str | None = None
    meter_reading: str | None = None
    notes: str | None = None


RAVI = DEMO_ACCOUNTS[1].username
ANITA = DEMO_EXTRA_ENGINEERS[0][0]

# A believable week: some jobs done, some running, some waiting to go out.
# Ravi is the persona visitors sign in as, so he gets a job in every state.
TASK_SPECS: tuple[_TaskSpec, ...] = (
    _TaskSpec(
        TaskType.SERVICE_CALL, "Sunrise Textiles", "Compressor CX-220", -4,
        TaskStatus.COMPLETED, engineer=ANITA, meter_reading="14820",
        notes="Replaced worn drive belt and re-tensioned. Running clean.",
    ),
    _TaskSpec(
        TaskType.SEND_MATERIAL, "Meridian Packaging", "Sealing head SH-9", -3,
        TaskStatus.COMPLETED, engineer=RAVI,
        notes="Two spare sealing blades handed over at the gate.",
    ),
    _TaskSpec(
        TaskType.SERVICE_CALL, "Everest Plastics", "Injection unit IP-75", -1,
        TaskStatus.COMPLETED, engineer=ANITA, meter_reading="9312",
        notes="Heater band replaced. Temperature holding steady.",
    ),
    _TaskSpec(
        TaskType.SERVICE_CALL, "Kaveri Cold Storage", "Condenser KC-4", 0,
        TaskStatus.IN_PROGRESS, engineer=ANITA, meter_reading="31770",
        notes="On site. Checking the low-pressure cut-out.",
    ),
    _TaskSpec(
        TaskType.SEND_MATERIAL, "Nandi Engineering Works", "Gearbox NG-12", 0,
        TaskStatus.IN_PROGRESS, engineer=RAVI,
        notes="Oil seals picked up, heading out after lunch.",
    ),
    _TaskSpec(
        TaskType.SERVICE_CALL, "Deccan Paper Mills", "Roller drive DR-30", 0,
        TaskStatus.ASSIGNED, engineer=RAVI,
        notes="Customer reports intermittent stalling under load.",
    ),
    _TaskSpec(
        TaskType.SERVICE_CALL, "Pioneer Rubber", "Mixer PR-500", 1,
        TaskStatus.ASSIGNED, engineer=ANITA,
        notes="Annual service. Carry the full filter set.",
    ),
    _TaskSpec(
        TaskType.SEND_MATERIAL, "Sunrise Textiles", "Compressor CX-220", 2,
        TaskStatus.ASSIGNED, engineer=RAVI,
        notes="Air filter cartridges, two units.",
    ),
    _TaskSpec(
        TaskType.SERVICE_CALL, "Coastal Foods", "Chiller CF-18", 3,
        TaskStatus.YET_TO_ASSIGN,
        notes="Callback logged this morning. Needs an engineer.",
    ),
    _TaskSpec(
        TaskType.SEND_MATERIAL, "Meridian Packaging", "Sealing head SH-9", 4,
        TaskStatus.YET_TO_ASSIGN,
        notes="Awaiting confirmation of the part number from the customer.",
    ),
)


# One quotation per seeded business, using the standard format. Prices are
# typed in by hand here exactly as the proprietor types them in the form:
# there is no price database and this seed does not pretend otherwise.
QUOTATION_SPECS: tuple[dict, ...] = (
    {
        "business_key": "arcot_enterprises",
        "customer_name": "Sunrise Textiles",
        "customer_address": "Plot 14, Industrial Estate, Coimbatore 641021",
        "notes": "Prices valid for 30 days. Delivery within two weeks of order.",
        "items": [
            {"particulars": "Air filter cartridge, CX series", "hsn_code": "8421",
             "price": "2450.00", "quantity": 2},
            {"particulars": "Drive belt, B-section", "hsn_code": "4010",
             "price": "1180.00", "quantity": 1},
            {"particulars": "On-site fitting and trial run", "hsn_code": "9987",
             "price": "3500.00", "quantity": 1},
        ],
    },
    {
        "business_key": "arcot_automations",
        "customer_name": "Deccan Paper Mills",
        "customer_address": "Survey 82/3, Mill Road, Erode 638002",
        "notes": "Commissioning support included for one day.",
        "items": [
            {"particulars": "VFD 7.5 kW with enclosure", "hsn_code": "8504",
             "price": "38900.00", "quantity": 1},
            {"particulars": "Control panel wiring and terminations", "hsn_code": "8537",
             "price": "9750.00", "quantity": 1},
        ],
    },
    {
        "business_key": "arcot_automations",
        "customer_name": "Everest Plastics",
        "customer_address": "24 SIDCO Nagar, Hosur 635109",
        "notes": "Taxes extra as applicable.",
        "items": [
            {"particulars": "Temperature controller, PID", "hsn_code": "9032",
             "price": "6400.00", "quantity": 3},
            {"particulars": "Thermocouple, K-type, 1m", "hsn_code": "9025",
             "price": "890.00", "quantity": 3},
        ],
    },
)


def _assert_demo_mode() -> None:
    """The guard that makes this command safe to have on disk.

    Seeding deletes data. Requiring DEMO_MODE means it can only ever run
    against the demo deployment, never against the real database.
    """
    if not get_settings().demo_mode:
        raise ValidationError(
            "Refusing to seed: DEMO_MODE is not enabled. "
            "This command only ever runs against the demo database."
        )


def _demo_usernames() -> list[str]:
    return [a.username for a in DEMO_ACCOUNTS] + [u for u, _ in DEMO_EXTRA_ENGINEERS]


def reset_demo(db: Session) -> None:
    """Remove everything a previous seed created, in foreign-key order."""
    _assert_demo_mode()

    db.execute(delete(QuotationItem))
    db.execute(delete(Quotation))
    db.execute(delete(Task))
    db.execute(delete(User).where(User.username.in_(_demo_usernames())))
    db.commit()


def seed_demo(db: Session, *, reset: bool = False) -> SeedSummary:
    """Create the demo accounts and their sample data.

    Without ``reset`` this is idempotent: existing demo users are reused and no
    duplicate tasks or quotations are added.
    """
    _assert_demo_mode()

    password = get_settings().demo_password
    if not password:
        raise ValidationError("Set DEMO_PASSWORD before seeding the demo.")

    if reset:
        reset_demo(db)

    users = UserRepository(db)
    auth = AuthService(db)
    already_seeded = users.get_by_username(DEMO_ACCOUNTS[0].username) is not None

    def ensure_user(username: str, full_name: str, role: UserRole) -> None:
        if users.get_by_username(username) is None:
            auth.create_user(
                username=username, full_name=full_name, role=role, password=password
            )

    for account in DEMO_ACCOUNTS:
        ensure_user(account.username, account.full_name, account.role)
    for username, full_name in DEMO_EXTRA_ENGINEERS:
        ensure_user(username, full_name, UserRole.SERVICE_ENGINEER)
    db.commit()

    if already_seeded:
        # Running the plain command twice must not double the sample data.
        return SeedSummary(users=len(_demo_usernames()), tasks=0, quotations=0)

    proprietor = users.get_by_username(DEMO_ACCOUNTS[0].username)
    engineers = {
        e.username: e.id for e in users.list_by_role(UserRole.SERVICE_ENGINEER)
    }

    return SeedSummary(
        users=len(_demo_usernames()),
        tasks=_seed_tasks(db, proprietor, engineers),
        quotations=_seed_quotations(db, proprietor),
    )


def _seed_tasks(db: Session, proprietor: User, engineers: dict[str, int]) -> int:
    service = TaskService(db)
    today = date.today()
    created = 0

    for spec in TASK_SPECS:
        assignee = engineers.get(spec.engineer) if spec.engineer else None

        task = service.create_task(
            proprietor,
            task_type=spec.task_type,
            scheduled_date=today + timedelta(days=spec.day_offset),
            customer_name=spec.customer_name,
            model=spec.model,
            meter_reading=spec.meter_reading,
            notes=spec.notes,
            assigned_engineer_id=assignee,
        )

        # Walk the real workflow instead of writing the status directly, so the
        # seeded data can only ever be in a state the application allows. The
        # details are set at creation because a completed task is read-only.
        for target in (TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED):
            if task.status is spec.status:
                break
            service.change_status(proprietor, task.id, target)

        created += 1

    return created


def _seed_quotations(db: Session, proprietor: User) -> int:
    service = QuotationService(db)
    businesses = {b.key: b for b in service.list_businesses()}
    created = 0

    for spec in QUOTATION_SPECS:
        business = businesses.get(spec["business_key"])
        if business is None:
            # The businesses come from a migration; skip rather than invent one.
            continue
        service.create_quotation(
            proprietor,
            business_id=business.id,
            template_key="standard",
            customer_name=spec["customer_name"],
            customer_address=spec["customer_address"],
            notes=spec["notes"],
            items=spec["items"],
        )
        created += 1

    return created
