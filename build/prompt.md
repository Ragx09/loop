LOOP — Local Operations & Optimization Platform

Build a web application called LOOP (Local Operations & Optimization Platform) for managing a small service business.

Important Scope Rule

Implement ONLY the functionality described in this document.

Do not add extra features, workflows, databases, dashboards, analytics, notifications, payment systems, inventory management, customer portals, or other functionality unless explicitly described here.

The application should be structured so additional features can be added later.

---

1. User Types

There are exactly two user types.

1.1 Proprietor / Admin

The proprietor is the business owner and has administrative access.

For this initial version, the proprietor should be able to:

- Create tasks
- View tasks
- Manage task status
- Generate quotations
- Download quotations as PDF

The proprietor is the primary user who receives customer calls and creates tasks.

---

1.2 Service Engineer

Service engineers are responsible for completing assigned service tasks.

From the service engineer side, they should be able to:

- View tasks assigned to them
- Update the relevant task information
- Move the task through its completion process
- Complete the task using a Complete action

The exact additional completion requirements will be defined later.

Do not invent those requirements now.

---

2. Task Management

The proprietor receives customer calls during the day.

A call can result in one of two task types:

1. Service Call
2. Sending Material

The proprietor should be able to create a task for either type.

---

3. Creating a Task

When the proprietor creates a task, the system should record:

Automatically generated

- Created Date
- Created Time

The created time should be generated automatically by the system.

Selected / entered by proprietor

- Task Type
  - Service Call
  - Sending Material
- Scheduled Date

The proprietor should be able to select the scheduled date using a calendar pop-up/date picker.

For example:

«Customer calls today → proprietor creates the task today → selects next Tuesday as the date on which the task should be completed.»

The task should therefore preserve both:

- When the task was created
- When the task is scheduled

---

4. Task Information

A task should contain the following information where applicable:

- Customer Name
- Model
- Meter Reading

These details are part of the information that the service engineer updates from the service engineer side after handling the call/task.

Do not create a price database or automatically determine these values.

---

5. Task Status

Every task should have a status.

The statuses are exactly:

1. Yet to Assign
2. Assigned
3. In Progress
4. Completed

Status flow

The intended basic flow is:

Yet to Assign → Assigned → In Progress → Completed

The service engineer should be able to perform the actions necessary to progress the task.

A task reaches Completed when the service engineer presses the Complete button after carrying out the required completion steps.

The exact completion requirements will be specified later.

Do not invent them now.

---

6. Task List

The proprietor should have a view where created tasks can be seen.

Each task should clearly show information such as:

- Task type
- Customer
- Scheduled date
- Created date/time
- Assigned engineer, when applicable
- Status

The UI should make it easy for the proprietor to understand which calls are:

- Yet to Assign
- Assigned
- In Progress
- Completed

Do not add analytics or extra dashboard functionality at this stage.

---

7. Generate Quotation

This functionality is available only to the Proprietor/Admin.

There should be an option called:

Generate Quotation

The proprietor should be able to create a quotation from this section.

---

8. Quotation Formats

There are 3–4 quotation formats/templates that will be provided separately.

There are also two business names:

- Arcat Enterprises
- Arcat Automations

The system should support generating quotations under these business names and using the provided quotatio