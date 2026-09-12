CLAUDE.md — LOOP

Project Identity

LOOP — Local Operations & Optimization Platform

LOOP is an internal business operations platform designed initially for a small service business.

The current core functionality consists of:

1. Task management
2. Service-call management
3. Material-sending task management
4. Service engineer task execution
5. Quotation generation
6. Multiple quotation formats/templates
7. Support for multiple business names

The application must be designed so that functionality can be expanded significantly in the future without requiring a rewrite of the existing system.

---

1. CORE DEVELOPMENT PRINCIPLE

LOOP is an evolving application.

Requirements will be added, changed, and refined frequently during development.

Therefore:

«Never optimize the codebase only for today's requirements. Build clean boundaries so tomorrow's requirements can be added without breaking yesterday's functionality.»

Every implementation should prioritize:

- Maintainability
- Modularity
- Clear separation of concerns
- Extensibility
- Simple code
- Testability
- Data integrity
- Backward compatibility
- Easy debugging
- Easy future modification

Avoid unnecessary complexity, but do not take shortcuts that make future changes difficult.

---

2. IMPORTANT RULE — DO NOT INVENT FEATURES

Only implement functionality explicitly requested by the user.

Do not independently add:

- Features
- Business rules
- Database fields
- Workflows
- Automation
- Notifications
- Integrations
- AI functionality
- Analytics
- Dashboards
- Permissions
- Pricing logic

unless they are required by an explicitly defined requirement or are technically necessary.

If a requirement is ambiguous and implementing it would materially affect architecture or business logic:

1. Identify the ambiguity.
2. Explain the impact.
3. Ask before introducing a significant business rule.

Do not silently make important assumptions.

---

3. REQUIREMENTS CHANGE MANAGEMENT

The user will continuously provide new requirements.

When a new requirement is provided:

First

Understand how it affects the existing system.

Then

Identify:

- Existing components affected
- Database changes required
- API changes required
- UI changes required
- Authentication/authorization implications
- Existing functionality that could break

Then

Implement the smallest clean change that satisfies the requirement.

Do not rewrite unrelated parts of the application.

Do not duplicate functionality simply because it is easier than modifying an existing component.

---

4. BEFORE MODIFYING EXISTING CODE

Before making a significant change:

1. Inspect the existing implementation.
2. Understand the relevant architecture.
3. Identify dependencies.
4. Check existing database models.
5. Check existing API routes/services.
6. Check existing UI components.
7. Reuse existing abstractions where appropriate.
8. Check whether tests exist.
9. Consider backward compatibility.

Never blindly overwrite existing functionality.

---

5. ARCHITECTURE

Use a clean layered architecture.

Keep these responsibilities separated:

Frontend

Responsible for:

- UI
- User interaction
- Form validation
- Displaying application state
- Calling backend APIs

Backend

Responsible for:

- Business logic
- Authentication
- Authorization
- Validation
- Task workflows
- Quotation generation
- Database operations

Database

Responsible for:

- Persistent application data
- Relationships
- Constraints
- Data integrity

File/Document Layer

Responsible for:

- Quotation templates
- Generated quotation PDFs
- Future document-related assets

Do not put business logic directly inside UI components when it belongs in the backend.

---

6. DATABASE

Use PostgreSQL as the primary database.

Do not use SQLite as the production architecture.

SQLite may be used temporarily for experiments or isolated tests if necessary, but the application architecture should target PostgreSQL.

Reasons:

- Multiple users
- Concurrent operations
- Reliable relational data
- Strong constraints
- Future deployment
- Better scalability
- Better support for structured business data
- Easier migration to a proper server environment

Use migrations for schema changes.

Never manually modify the production database schema without updating the migration system.

---

7. DATABASE DESIGN PRINCIPLES

Use normalized relational data where appropriate.

Important entities currently include:

User

Possible fields include:

- ID
- Name
- Role
- Authentication information

Roles currently include:

- PROPRIETOR
- SERVICE_ENGINEER

Task

Current conceptual fields:

- ID
- Task type
- Customer name
- Model
- Meter reading
- Created date
- Created time
- Scheduled date
- Assigned engineer
- Status

Task types:

- SERVICE_CALL
- SEND_MATERIAL

Task statuses:

- YET_TO_ASSIGN
- ASSIGNED
- IN_PROGRESS
- COMPLETED

Do not unnecessarily combine unrelated entities into one table.

Use foreign keys for relationships.

Use database constraints where they protect data integrity.

---

8. TASK WORKFLOW

The current task workflow is:

YET_TO_ASSIGN
      ↓
ASSIGNED
      ↓
IN_PROGRESS
      ↓
COMPLETED

Do not add additional statuses without an explicit requirement.

The workflow should be implemented in a way that allows additional statuses or transitions to be introduced later without rewriting the entire task system.

---

9. USER ROLES

There are currently two roles.

PROPRIETOR

The proprietor can:

- Create tasks
- View tasks
- Assign tasks
- Manage task workflow
- Generate quotations

SERVICE_ENGINEER

The service engineer can:

- View their assigned tasks
- Update relevant task information
- Progress the task
- Complete the task

Authorization must be enforced on the backend.

Do not rely only on frontend route hiding for security.

A user must not gain access to a protected API simply by manually calling the endpoint.

---

10. AUTHENTICATION

Implement authentication in a way that supports multiple users.

The system must distinguish users by role.

The architecture should allow more service engineers to be added later.

Do not hard-code a single engineer account into the application.

Do not hard-code the proprietor's identity into business logic.

---

11. LOCAL DEVELOPMENT ENVIRONMENT

During the initial building phase, LOOP will primarily run on a laptop.

The laptop should act as the local application server.

Preferred architecture:

                  LAPTOP
                     │
        ┌────────────┴────────────┐
        │                         │
   LOOP Backend              PostgreSQL
        │
        │
   LOOP Frontend
        │
        └───────────────┐
                        │
              Browser sessions
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   Proprietor       Engineer 1      Engineer 2
      login            login           login

Multiple users should be able to use the application through their own authenticated accounts.

Do NOT create completely separate codebases or databases for different roles.

The application should be a single system with role-based access.

---

12. LOCAL SERVER REQUIREMENTS

During development:

- Backend runs locally
- Frontend runs locally
- PostgreSQL runs locally
- Database persists independently of the frontend
- Users access LOOP through a browser

The architecture should make it straightforward to later move:

Laptop
   ↓
Cloud / VPS / Production Server

without redesigning the entire application.

Avoid hard-coding:

- localhost URLs
- database credentials
- file paths
- environment-specific configuration

Use environment variables.

---

13. ENVIRONMENT VARIABLES

Configuration that changes between environments must use environment variables.

Examples:

DATABASE_URL
JWT_SECRET
API_URL
APP_ENV
PORT

Never commit secrets into source control.

Provide a safe ".env.example".

Never place real credentials inside:

- Source code
- CLAUDE.md
- Documentation
- Git commits

---

14. QUOTATION SYSTEM

Quotation generation is an important part of LOOP.

The proprietor should be able to generate quotations under different business names and using different quotation formats.

Current business names:

- Arcat Enterprises
- Arcat Automations

There are currently approximately 3–4 quotation formats/templates.

More formats may be added later.

Therefore:

«DO NOT hard-code quotation layouts directly into the main application logic.»

Quotation generation must be designed as a modular system.

Conceptually:

Quotation
     │
     ├── Business
     │
     ├── Template
     │
     └── Quotation Data
             │
             ├── Customer
             ├── HSN Code
             ├── Particulars
             └── Price

The system should allow a new quotation format to be introduced without rewriting the entire quotation system.

---

15. QUOTATION TEMPLATES

Treat each quotation format as a separate template.

Example conceptual structure:

quotation/
    templates/
        template-a/
        template-b/
        template-c/
        template-d/

The exact implementation can differ depending on the chosen PDF-generation technology.

However, keep:

- Template definition
- Business information
- Quotation data
- PDF generation

properly separated.

Do not duplicate the entire quotation-generation engine for every template.

---

16. QUOTATION DATA

The proprietor enters quotation information manually.

Current information includes:

- Customer
- HSN Code
- Particulars/Product
- Price

Price must remain manually enterable.

There is currently:

«NO PRICE DATABASE.»

Do not introduce automatic pricing.

Do not assume that a product always has the same price.

The same product may have different prices for different customers.

---

17. QUOTATION PDF GENERATION

The system should generate a PDF based on:

Selected Business
        +
Selected Template
        +
Entered Quotation Data
        ↓
Generated PDF

The generated PDF should be downloadable.

Quotation generation should be isolated enough that the PDF-generation implementation can be changed later if required.

---

18. QUOTATION FORMAT FILES

When the user provides quotation samples/templates:

1. Inspect them carefully.
2. Identify their structure.
3. Identify fixed information.
4. Identify variable fields.
5. Identify table structure.
6. Identify formatting requirements.
7. Reproduce the format accurately.

Do not assume that all quotation formats have the same structure.

Each format may have different:

- Headers
- Business information
- Tables
- Fields
- Layout
- Footer
- Terms
- Styling

Treat templates independently while sharing common quotation data and generation infrastructure.

---

19. FILE ORGANIZATION

Keep the project organized.

Avoid creating large files containing unrelated responsibilities.

Prefer:

frontend/
backend/
database/
quotation/
templates/
tests/
docs/

Exact folder structure may depend on the selected technology stack.

The principle is more important than the exact names:

«One component should have one clear responsibility.»

---

20. API DESIGN

Backend APIs should be:

- Predictable
- Consistent
- RESTful where appropriate
- Properly validated
- Properly authorized
- Easy to extend

Do not put complex business logic directly inside route/controller functions.

Prefer:

Route / Controller
        ↓
Service / Business Logic
        ↓
Repository / Data Access
        ↓
Database

The exact implementation can vary according to the chosen framework.

---

21. VALIDATION

Validate data at appropriate layers.

Frontend validation improves user experience.

Backend validation protects the system.

Never assume that frontend validation is sufficient.

Examples:

- Required fields
- Valid dates
- Valid task types
- Valid task statuses
- Valid user roles
- Valid quotation values

---

22. ERROR HANDLING

Errors should be:

- Clear
- Predictable
- User-friendly
- Logged appropriately

Do not expose sensitive backend information to users.

Do not silently swallow important errors.

---

23. TESTING

Whenever a meaningful feature is implemented:

- Test the normal flow
- Test invalid input
- Test authorization
- Test important edge cases
- Test that existing functionality still works

For important business logic, create automated tests where practical.

Particularly test:

- Task status transitions
- Role permissions
- Task assignment
- Quotation calculations/data
- PDF generation
- Template selection

---

24. GIT / VERSION CONTROL

Use Git.

Make changes in small, understandable commits.

Commit messages should describe what changed.

Do not commit:

- ".env"
- Passwords
- API keys
- Generated secrets
- Temporary files
- Large unnecessary generated artifacts

Keep ".gitignore" updated.

---

25. DOCUMENTATION

Important architectural decisions should be documented.

If a major architectural decision changes, update the relevant documentation.

Do not allow documentation to become contradictory to the actual implementation.

Keep documentation concise and useful.

---

26. CLAUDE CODE WORKFLOW

When working on LOOP, follow this process.

Step 1 — Understand

Read:

- CLAUDE.md
- Relevant project documentation
- Existing implementation
- Relevant database schema
- Relevant tests

Step 2 — Plan

Before significant implementation, determine:

- What needs to change?
- Why?
- Which files/components are affected?
- Does the database need modification?
- Does the API need modification?
- Does the frontend need modification?
- Could existing functionality break?

Step 3 — Implement

Make the smallest clean implementation that satisfies the requirement.

Step 4 — Verify

Run:

- Relevant tests
- Type checking
- Linting
- Build
- Application checks

as applicable to the project.

Step 5 — Review

Before finishing:

- Check for unnecessary code
- Check for duplicated logic
- Check security
- Check authorization
- Check database integrity
- Check that existing functionality still works

---

27. DO NOT OVERENGINEER

LOOP is initially an internal business application.

Do not introduce distributed systems, microservices, message queues, Kubernetes, complex infrastructure, or other enterprise architecture unless the actual requirements justify them.

Prefer a well-structured modular monolith initially.

A strong starting architecture is:

Frontend
   │
   ▼
Backend API
   │
   ├── Authentication
   ├── Task Module
   ├── User Module
   └── Quotation Module
   │
   ▼
PostgreSQL

This can later be scaled if required.

---

28. FUTURE DEPLOYMENT

The initial application runs on a laptop.

The architecture should allow eventual deployment to a server/VPS/cloud environment.

Future deployment should conceptually become:

Users
  │
  ▼
Internet
  │
  ▼
Production Server
  │
  ├── Frontend
  ├── Backend
  └── PostgreSQL

The application should not require major architectural changes to make this transition.

---

29. BACKWARD COMPATIBILITY

When adding a new feature:

«Existing tasks, users, quotations, and functionality must continue working unless the user explicitly requests a breaking change.»

Database migrations must preserve existing data.

Do not delete or rename existing database fields simply because a new design seems cleaner.

If a breaking change is genuinely required:

1. Explain why.
2. Identify affected functionality.
3. Create an appropriate migration strategy.

---

30. SECURITY

Even though LOOP is initially a local business application:

Treat security seriously.

Implement:

- Authentication
- Role-based authorization
- Password hashing
- Secure session/token handling
- Backend authorization
- Input validation
- Protected database access

Never store plaintext passwords.

Never trust role information sent by the frontend.

---

31. DESIGN PHILOSOPHY

LOOP should feel like a practical business tool.

Prioritize:

- Speed
- Clarity
- Simplicity
- Low cognitive load
- Minimal clicks
- Clear statuses
- Easy task creation
- Easy quotation creation

Avoid unnecessary visual complexity.

---

32. CURRENT PRODUCT SCOPE

The current system contains:

Proprietor

- Create task
- Select task type
- Select scheduled date
- View tasks
- Assign tasks
- Manage task status
- Generate quotation
- Select business
- Select quotation format
- Enter quotation information
- Generate PDF
- Download PDF

Service Engineer

- Login
- View assigned tasks
- Update task information
- Progress task
- Complete task

Task types

- Service Call
- Sending Material

Task statuses

- Yet to Assign
- Assigned
- In Progress
- Completed

Business names

- Arcat Enterprises
- Arcat Automations

Quotation fields currently required

- Customer
- HSN Code
- Particulars/Product
- Price

---

33. FINAL RULE

When the user gives a new requirement, do not immediately start changing random files.

First understand how it fits into LOOP's architecture.

Build the feature in a way that:

New Requirement
       ↓
Existing Architecture
       ↓
Small Modular Change
       ↓
Tests
       ↓
Working LOOP

The goal is not merely to make the current feature work.

The goal is to build LOOP into a maintainable platform that can continuously evolve with the business.