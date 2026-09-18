# LOOP — How the UI is Connected

This document explains how a click in the browser reaches the database and comes
back as a page, and where to edit when you want the UI to look or behave
differently. Read the "Change recipes" section if you only want to change
something.

---

## 1. The shape of the system

LOOP serves **two front doors over one backend**:

```
                    ┌──────────────────────────────┐
  Browser ─────────▶│  /…      server-rendered UI  │──┐
  (people)          │          app/web/…           │  │
                    ├──────────────────────────────┤  │   one shared
  Future clients ──▶│  /api/…  JSON REST API       │──┤   service layer
  (app, script)     │          app/api/…           │  │
                    └──────────────────────────────┘  │
                                                      ▼
                                          app/services/…   business rules
                                                      │
                                          app/repositories/…  queries
                                                      │
                                                 PostgreSQL
```

The important consequence: **the UI is a thin layer.** It decides what is
displayed, never what is allowed or what a rule means. Both front doors call the
same services, so a rule can never differ between the web page and the API, and
replacing the UI later does not touch business logic.

---

## 2. One request, end to end

Example: the proprietor opens **Tasks** in the top bar.

```
1. Browser            GET /tasks   (session cookie attached automatically)
2. app/web/routes/tasks.py::task_list
      · CurrentUser dependency  → app/core/deps.py decodes the cookie and
        re-reads the user (and role) from the database — a role sent by the
        browser is never trusted
      · DbSession dependency    → request-scoped SQLAlchemy session
3. app/services/task_service.py::list_for_user
      · applies the rule "an engineer sees only their own tasks"
4. app/repositories/task_repository.py  → SQL → PostgreSQL
5. Back in the route: build the template context
      {"current_user": …, "tasks": …, "statuses": …, "counts": …}
6. app/web/templating.py  renders app/web/templates/tasks/list.html
      · the template extends base.html (the page shell)
      · base.html asks app/web/navigation.py which links this role may see
7. HTML → browser, styled by /static/theme.css + /static/app.css
```

Forms work the same way in reverse: a `<form method="post">` posts to a route,
the route calls a service, and the route answers with a `303` redirect to the
page that should now be shown (so a refresh never re-submits).

---

## 3. Where everything lives

| Concern | File | Change it when |
|---|---|---|
| Page shell: `<head>`, top bar, theme toggle | `app/web/templates/base.html` | The frame around every page changes |
| Top-bar links (and who sees them) | `app/web/navigation.py` | Adding/renaming/reordering navigation |
| Home page tiles | `app/web/tools.py` | Adding/renaming a tool on the launcher |
| Brand name & tagline, date/money helpers, template globals | `app/web/templating.py` | Wording or a new template helper |
| Colours, shadows, both themes | `app/web/static/theme.css` | Restyling the application |
| Component and layout rules | `app/web/static/app.css` | A component should look different |
| Individual screens | `app/web/templates/**.html` | One page's content changes |
| Which URL renders which screen | `app/web/routes/*.py` | Adding a page, or a form field |
| Rules, permissions, workflow | `app/services/*.py` | Behaviour changes (**not** the UI) |
| Status/type/role display names | `app/domain/enums.py` | "In Progress" should read differently |
| Demo sign-in options on the login page | `app/demo/accounts.py` | Adding/renaming a demo persona (see `docs/DEMO.md`) |

Quotation **PDF** templates are a separate system (`app/quotation/templates/`).
They are print documents, not screens, and share nothing with the CSS above —
see `CLAUDE.md` §15.

---

## 4. The template contract

Every page template starts with:

```jinja
{% extends "base.html" %}
{% block title %}Tasks — {{ brand_name }}{% endblock %}
{% block content %} … {% endblock %}
```

`base.html` renders the shell and needs exactly one context key:

* **`current_user`** — the signed-in `User`, or `None`. When it is `None` the
  top bar is not rendered (that is how the sign-in and error pages stay bare).
  **Every route that renders a page must pass it.**

Available in *all* templates, with no route changes needed
(registered in `app/web/templating.py`):

| Name | What it gives you |
|---|---|
| `brand_name`, `brand_tagline` | Product wording. The name comes from the `APP_NAME` environment variable |
| `stylesheets` | The stylesheet list `base.html` links, in order |
| `nav_for(role)` | Top-bar links this role may see |
| `now()` | Current date/time, evaluated at render time |
| `TaskStatus`, `TaskType` | Enums, so templates never hard-code strings |
| `| money` | `1234.5` → `1,234.50` |
| `demo_notice` | Wording of the demo strip, or `None` on a real instance |

Three rules keep the UI replaceable:

1. **No business logic in templates.** A template may ask "is this user a
   proprietor?" to decide what to *show*; it must never decide what is
   *allowed*. Authorization lives in the route dependency (`CurrentUser`,
   `Proprietor`) **and** again in the service.
2. **No literal colours in `app.css`.** Add a token to `theme.css` and use
   `var(--token)`, or the dark theme will silently break.
3. **No duplicated labels.** Display names come from the enum's `.label`.

---

## 5. Change recipes

### Restyle the application (colours, dark mode)

Edit `app/web/static/theme.css` only. Every rule refers to these tokens, so one
edit changes the whole app in both themes. Hard-refresh the browser
(`Ctrl+F5`) — stylesheets are cached, HTML is not.

### Change how a component looks (cards, tables, buttons)

Edit `app/web/static/app.css`. Use existing tokens; do not write a raw colour.

### Add, rename or reorder a top-bar link

Edit the `NAV_LINKS` tuple in `app/web/navigation.py`:

```python
NavLink("Reports", "/reports", PROPRIETOR_ONLY),
```

No template change. `roles` controls visibility only — the page itself still
needs its own authorization.

### Add a tile to the home launcher

Append a `Tool(...)` in `app/web/tools.py` (icon is inline SVG path data).

### Rename the product

Set `APP_NAME` in `.env`; edit `brand_tagline` in `app/web/templating.py`.

### Add a new page

1. Create `app/web/templates/<area>/<page>.html` extending `base.html`.
2. Add the route in `app/web/routes/<area>.py`, passing `current_user`:

   ```python
   @router.get("/reports")
   def reports(request: Request, db: DbSession, user: Proprietor):
       return templates.TemplateResponse(
           request, "reports/list.html",
           {"current_user": user, "rows": ReportService(db).list_for(user)},
       )
   ```
3. If the file is a **new** area, register its router in `app/web/router.py`.
4. Make it reachable: add a `NavLink` and/or a `Tool`.
5. Put the rules in a service — not in the route, not in the template.
6. Add a render check to `tests/test_web_pages.py`.

### Add a field to an existing form

Three coordinated edits: the `<input>` in the template, the `Form(...)`
parameter in the route, and the argument in the service (plus a model column and
an Alembic migration if it is stored). Keep the new field optional so existing
records still load — see `CLAUDE.md` §29.

### Replace the UI entirely (React, mobile app, …)

Nothing in `app/web/` is load-bearing. `/api/…` already exposes login, tasks,
users and quotations as JSON with the same authorization, so a new frontend can
be built against it and `app/web/` deleted without touching services, models or
migrations. That is the reason the two front doors exist.

---

## 6. Working on the UI

```bash
# PostgreSQL
docker compose up -d db

# Backend + UI, auto-reloading on any change under app/
.venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    --reload --reload-dir app
```

* **Template edits** appear on the next page load — no restart.
* **Python edits** restart the server automatically (watch the log for
  `Reloading`; if a page renders with blank values, the worker is stale —
  restart it).
* **CSS edits** need a hard refresh.
* Pages are at `http://localhost:8000`; other devices on the same network use
  the laptop's LAN address (see `docs/RUNNING.md`).

Page rendering is covered by `tests/test_web_pages.py`, which asserts the shell
renders and that each role is offered only its own links:

```bash
.venv/Scripts/python -m pytest tests/test_web_pages.py -q
```

Run the whole suite before committing UI changes — the API tests prove the
service layer still behaves while the UI moves.
