# Running LOOP Locally

The laptop is the application server: PostgreSQL and the backend run on it, and
everyone (proprietor and engineers) uses LOOP through a browser.

```
                 LAPTOP
      ┌────────────────────────────┐
      │  uvicorn  :8000            │
      │  PostgreSQL (Docker) :5433 │
      └────────────┬───────────────┘
                   │  Wi-Fi / LAN
      ┌────────────┼────────────┐
  Proprietor   Engineer 1   Engineer 2
    browser      browser      browser
```

## 1. Configuration

Copy `.env.example` to `.env` and fill it in. Nothing environment-specific
belongs in the code. The host port for PostgreSQL is `POSTGRES_PORT` and must
match the port in `DATABASE_URL`.

Generate a real secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"   # → JWT_SECRET
```

## 2. Start the database

```bash
docker compose up -d db          # PostgreSQL only; the app runs on the host
docker compose ps                # wait for "healthy"
```

## 3. Apply migrations

```bash
.venv/Scripts/python -m alembic upgrade head
```

## 4. Create users

Users are never hard-coded. Create them once:

```bash
.venv/Scripts/python scripts/manage.py create-user \
    --username owner --name "Proprietor Name" --role PROPRIETOR
.venv/Scripts/python scripts/manage.py create-user \
    --username engineer1 --name "Engineer One" --role SERVICE_ENGINEER

.venv/Scripts/python scripts/manage.py list-users
```

Omit `--password` and set `LOOP_INITIAL_PASSWORD` instead, so passwords stay out
of the shell history.

## 5. Start the application

```bash
.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    --reload --reload-dir app
```

`--host 0.0.0.0` listens on every network interface (not just this laptop) and
`--reload` restarts on code changes. Check it:

```bash
curl http://localhost:8000/health      # {"status":"ok","app":"LOOP"}
```

Then open `http://localhost:8000`.

## 6. Access from other devices on the network

The server already listens on the LAN; Windows Firewall is what blocks other
devices. Allow the port **once**, in an *Administrator* PowerShell:

```powershell
# Mark the home/office Wi-Fi as a private network (not "Public")
Set-NetConnectionProfile -InterfaceAlias 'Wi-Fi' -NetworkCategory Private

# Allow LOOP's port on private networks only
New-NetFirewallRule -DisplayName 'LOOP (port 8000)' -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 8000 -Profile Private
```

Find the laptop's address and share it:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object InterfaceAlias -eq 'Wi-Fi' | Select-Object IPAddress
```

Engineers then open `http://<laptop-ip>:8000` — for example
`http://192.168.7.4:8000`. The address is handed out by DHCP, so it can change
when the laptop reconnects; reserve a static lease on the router (or set a
static IP) if it needs to be stable.

Notes:

* Everyone must be on the **same** Wi-Fi/LAN. This is not internet access.
* The laptop must stay awake and the server running.
* Sessions ride on a cookie that is not marked `secure` outside production, so
  plain `http://` works on the LAN. Before exposing LOOP to the internet, set
  `APP_ENV=production` and put it behind HTTPS.

## 7. Tests

```bash
.venv/Scripts/python -m pytest -q
```

Tests use an isolated SQLite file by default, so they never touch development
data. Set `TEST_DATABASE_URL` to a PostgreSQL URL to run them against the real
target database.

## 8. Everything in one container (optional)

`docker compose up --build` also runs the backend in Docker (migrations
included). Convenient for a demo, but code changes then need a rebuild — for
day-to-day development prefer the database-only setup above.

## 9. Stopping

```
Ctrl+C            # the backend
docker compose stop db      # keeps the data
docker compose down         # removes containers; the named volume keeps data
```
