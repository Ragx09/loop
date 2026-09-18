# LOOP — Claude Code Build Prompt

> Copy everything below the line into Claude Code (as your project prompt / initial instruction, or save as `CLAUDE.md` in the repo root) to kick off end-to-end development.

---

## SYSTEM CONTEXT

You are building **LOOP**, a service-business operating system for small-to-mid service/repair/installation businesses (e.g. industrial motor/automation service companies). The product lets a **proprietor/admin** run the entire business from one dashboard, and lets **engineers** execute field jobs from their phones.

Core business loop to support end-to-end:

```
Customer → Quotation → Invoice → Payment
Customer → Service Call → Engineer Assignment → Field Execution → Materials Used → Service Report
```

Treat this as **one connected business data graph**, not a set of disconnected CRUD screens:

```
                    CUSTOMER
                       │
          ┌────────────┼────────────┐
          │            │            │
       EQUIPMENT    QUOTATION     SERVICE CALL
                       │              │
                       ▼              ▼
                    INVOICE        ENGINEER
                       │              │
                       ▼              ▼
                    PAYMENT       MATERIAL USED
                                      │
                                      ▼
                                  INVENTORY
```

Every module must reference this shared graph via foreign keys — do not build isolated features.

---

## ARCHITECTURE PRINCIPLES (non-negotiable)

1. **Modular monolith.** No microservices, no Kubernetes, no Kafka, no Redis, no message queues. A single Next.js app with clearly separated modules is correct for this scale.
2. **Separation of concerns** inside the monolith:
   - `app/` — routes, pages, layouts (UI only)
   - `modules/<domain>/` — business logic per domain (customers, tasks, quotations, invoices, payments, inventory, engineers, businesses, ai)
   - `lib/db/` — database client, schema, migrations
   - `lib/pdf/` — PDF generation, isolated from business logic
   - `lib/ai/` — LLM calls, isolated and optional (app must work with AI features disabled)
3. **Multi-business support from day one.** Every business-owned record (customers, quotations, invoices, inventory, etc.) has a `business_id`. The active business is set by a top-level switcher and enforced in every query (Postgres Row-Level Security or explicit `WHERE business_id = ...` — pick RLS if using Supabase Auth).
4. **Two roles only for V1:** `owner/admin` and `engineer`. Design the auth/permission model so more roles can be added later without a rewrite.
5. **Data integrity & backward compatibility.** Don't redesign existing task/status models. Extend them. Migrations must be additive and reversible.
6. **No invented pricing logic.** There is no price database or auto-pricing engine. All prices are manually entered by the admin, including when AI assists with drafting a quotation.
7. **AI is optional and additive.** The app must be fully functional with AI features/environment variables absent. AI never writes final prices; it only drafts text/structure for human review.

---

## TECH STACK (use exactly this unless a stated constraint forces otherwise)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + TypeScript |
| UI | Tailwind CSS + shadcn/ui + Lucide icons |
| Charts | Recharts |
| Backend | Next.js Route Handlers / Server Actions (no separate backend server) |
| Database | PostgreSQL via Supabase |
| ORM | Drizzle (preferred) or Prisma — pick one and use it consistently |
| Auth | Supabase Auth (email/password to start; magic link optional) |
| File storage | Supabase Storage (photos, PDFs, signatures) |
| PDF generation | `@react-pdf/renderer` or Puppeteer/HTML-to-PDF, isolated in `lib/pdf/` |
| Validation | Zod (shared schemas between client and server) |
| AI | OpenAI API (or configurable provider), called only from `lib/ai/`, feature-flagged |
| Hosting | Vercel |
| Error monitoring | Sentry |
| Source control | GitHub, conventional commits, one PR per module/phase |

Do not introduce Docker orchestration, custom job queues, or additional infra services for V1.

---

## DATA MODEL (build these tables/entities first)

- `businesses` (id, name, gstin, address, logo_url, bank_details, created_at)
- `users` (id, auth_id, name, role[owner|engineer], phone, business_id)
- `customers` (id, business_id, name, phone, email, address, gstin)
- `equipment` (id, customer_id, name, model, serial_number, installed_at)
- `service_calls` (id, business_id, customer_id, equipment_id, problem_description, priority, scheduled_at, assigned_engineer_id, status, meter_reading, notes)
- `materials_used` (id, service_call_id, inventory_item_id, quantity)
- `service_reports` (id, service_call_id, work_performed, meter_reading, materials_summary, photos[], customer_signature_url, pdf_url, created_at)
- `quotations` (id, business_id, customer_id, quote_number, line_items jsonb, subtotal, tax, total, status[draft|sent|accepted|rejected], pdf_url, created_at)
- `invoices` (id, business_id, customer_id, quotation_id nullable, invoice_number, line_items jsonb, subtotal, gst_breakdown jsonb, total, status[pending|partially_paid|paid|overdue], pdf_url, created_at)
- `payments` (id, invoice_id, amount, method, paid_at, notes)
- `inventory_items` (id, business_id, sku, name, category, hsn, purchase_price, selling_price, stock_qty, min_stock)
- `activity_log` (id, business_id, entity_type, entity_id, actor_id, action, description, created_at)
- `notifications` (id, user_id, message, type, read_at, created_at)

Keep the existing task/status enums intact and extend them rather than replacing them.

---

## BUILD PHASES — implement strictly in this order, each phase should be a working, demoable slice

### Phase 0 — Foundation
- Next.js + TypeScript scaffold, Tailwind + shadcn/ui setup
- Supabase project, Postgres schema/migrations for the data model above
- Supabase Auth wired up with `owner` and `engineer` roles
- Business switcher (top nav) that scopes all subsequent queries to `business_id`
- Global layout shell: sidebar nav (admin) + mobile-first shell (engineer)

### Phase 1 — Customer CRM
- Customer list + detail page
- Equipment records nested under a customer
- Customer history panel (service calls, quotations, invoices, lifetime value) — read-only rollups for now

### Phase 2 — Service Calls & Task Assignment (extend, don't replace, existing task system)
- Create service call: Customer → Equipment → Problem → Priority → Schedule → Assign engineer
- Admin "Today's Schedule" table (time, customer, engineer, job type, status)
- Status transitions preserved from existing model

### Phase 3 — Engineer Mobile View
- "My Jobs" list for the logged-in engineer, today + upcoming
- Job detail: problem, meter reading, `Start Job`
- In-progress job: add materials used (decrements inventory), notes, photo upload, customer signature capture
- `Complete Job` → auto-generates a Service Report record + PDF

### Phase 4 — Quotations
- Quotation builder: customer, line items, tax, total, multiple templates
- Quotation PDF generation, branded per active business
- Status flow: draft → sent → accepted/rejected

### Phase 5 — Invoicing & Payments
- `Convert Quotation to Invoice` action
- Standalone invoice creation (for the Smart POS flow below)
- Invoice PDF with GST breakdown (CGST/SGST/IGST), HSN/SAC, bank details
- Record full/partial payments; auto-compute status (pending/partially paid/paid/overdue)
- Payments dashboard: outstanding, due this week, overdue, collected today

### Phase 6 — Inventory & Smart POS
- Inventory CRUD with stock levels and minimum-stock flags
- Material dispatch record (separate from service-call material usage) that decrements stock
- Smart POS screen: search product/service → cart → GST calc → `Generate Invoice`

### Phase 7 — Owner Dashboard & Analytics
- Command Center: today's jobs summary, quick actions, today's schedule
- Business Overview: revenue, outstanding, service call counts, completed count, customer count
- Charts: revenue by month, service calls by month, top customers, revenue by service/product, engineer completion counts

### Phase 8 — Cross-cutting polish
- Global search (`⌘K`) across customers, invoices, quotations, equipment, engineers
- Activity timeline per customer/job (auto-logged from every state-changing action)
- Notifications (in-app only, no SMS/WhatsApp for V1): job completed, invoice overdue, dispatch created, quotation generated
- Document Center: unified, searchable list of all quotations/invoices/service reports/dispatches, filterable by customer

### Phase 9 — AI features (feature-flagged, optional)
- AI Service Summary: engineer's rough notes → clean professional summary (editable before saving)
- AI Quotation Assistant: free-text description → structured draft line items (particular/service/qty) — price fields always left blank for manual entry
- AI Customer Summary: short natural-language rollup of a customer's service history/patterns
- All AI calls isolated in `lib/ai/`; app must build and run with `AI_ENABLED=false`

---

## DEMO SCRIPT TO VALIDATE AGAINST

After each phase, the following end-to-end flow should get incrementally more complete, and must fully work after Phase 7:

1. Owner creates customer **ABC Industries**.
2. Owner creates a quotation (motor + installation), generates PDF.
3. Owner converts quotation → invoice.
4. Owner creates a service call linked to the invoice/customer, assigns engineer **Ravi**.
5. Ravi opens "My Jobs" on phone, taps **Start Job**.
6. Ravi enters meter reading, adds material used (bearing ×2 — inventory auto-decrements), writes notes, uploads a photo, captures signature, taps **Complete Job**.
7. LOOP auto-generates the Service Report PDF.
8. Owner's dashboard updates in real time: service call marked complete, invoice shows ₹X paid / ₹Y outstanding after a payment is recorded.

Use this script as your acceptance test for the MVP milestone.

---

## EXPLICIT NON-GOALS FOR V1

- No microservices/Kubernetes/Kafka/Redis/queues
- No real payment gateway integration (status is manually recorded: pending/partial/paid)
- No SMS/WhatsApp notifications
- No automatic/AI-driven pricing — all prices are human-entered
- No RAG/vector database for AI features
- No roles beyond `owner` and `engineer`

---

## DELIVERY EXPECTATIONS

- Each phase = one or more small PRs, not one giant commit.
- Write Zod schemas once and reuse for client-side forms and server-side validation.
- Every business-scoped table must be protected by `business_id` filtering (RLS preferred).
- Seed script with 1 demo business, 2 engineers, 5 customers, sample quotations/invoices/inventory so the demo script above can be run immediately after setup.
- README with setup steps (Supabase project creation, env vars, migration commands, seed command, `npm run dev`).

Build Phase 0 now, and stop after each phase for review before proceeding to the next.
