"""Small administrative CLI for LOOP.

Users are created here rather than being hard-coded anywhere in the app.

    python scripts/manage.py create-user --username raghav --name "Raghavendra" \
        --role PROPRIETOR --password "..."
    python scripts/manage.py list-users
    python scripts/manage.py seed-demo [--reset]

If --password is omitted the value of the LOOP_INITIAL_PASSWORD environment
variable is used, so credentials never need to appear in shell history.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.errors import LoopError  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.demo.seed import seed_demo  # noqa: E402
from app.domain.enums import UserRole  # noqa: E402
from app.services.auth_service import AuthService  # noqa: E402


def create_user(args: argparse.Namespace) -> int:
    password = args.password or os.getenv("LOOP_INITIAL_PASSWORD")
    if not password:
        print("No password given: pass --password or set LOOP_INITIAL_PASSWORD.")
        return 2

    with SessionLocal() as db:
        service = AuthService(db)
        try:
            user = service.create_user(
                username=args.username,
                full_name=args.name,
                role=UserRole(args.role),
                password=password,
            )
            db.commit()
        except LoopError as exc:
            print(f"Could not create user: {exc.message}")
            return 1
        print(f"Created {user.role.label}: {user.username} (id={user.id})")
    return 0


def list_users(_: argparse.Namespace) -> int:
    from sqlalchemy import select

    from app.models.user import User

    with SessionLocal() as db:
        users = db.execute(select(User).order_by(User.id)).scalars().all()
        if not users:
            print("No users yet.")
        for user in users:
            state = "active" if user.is_active else "disabled"
            print(f"{user.id:>3}  {user.username:<20} {user.role.value:<16} {state}")
    return 0


def seed_demo_command(args: argparse.Namespace) -> int:
    """Populate the public demo with sample data.

    Only ever runs when DEMO_MODE is enabled, so it cannot touch a real
    database by accident — the guard lives in app/demo/seed.py.
    """
    with SessionLocal() as db:
        try:
            summary = seed_demo(db, reset=args.reset)
        except LoopError as exc:
            print(f"Could not seed the demo: {exc.message}")
            return 1
        print(
            f"Demo ready: {summary.users} users, {summary.customers} customers, "
            f"{summary.tasks} tasks, {summary.quotations} quotations, "
            f"{summary.invoices} invoices, {summary.inventory} inventory items."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LOOP management commands")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-user", help="Create a proprietor or service engineer")
    create.add_argument("--username", required=True)
    create.add_argument("--name", required=True, help="Full name")
    create.add_argument("--role", required=True, choices=[r.value for r in UserRole])
    create.add_argument("--password", default=None)
    create.set_defaults(func=create_user)

    listing = sub.add_parser("list-users", help="List existing users")
    listing.set_defaults(func=list_users)

    demo = sub.add_parser("seed-demo", help="Seed the public demo with sample data")
    demo.add_argument(
        "--reset",
        action="store_true",
        help="Wipe the existing demo data first, returning the demo to a clean state",
    )
    demo.set_defaults(func=seed_demo_command)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
