# SupplyPilot

> **AI-powered procurement decision intelligence for high-stakes
> purchasing operations.**

SupplyPilot is a full-stack AI procurement agent that investigates
purchasing recommendations against live operational evidence, applies
business and procurement constraints, requests human authorization when
required, executes the approved purchase action, and validates the
resulting purchase order.

The core idea: **don't blindly execute an ERP recommendation ---
investigate it, constrain it, explain it, authorize it, and verify the
outcome.**

## What SupplyPilot Does

A purchasing case can begin with a system recommendation such as:

> **Buy 800 units of Hydraulic Pump Cartridge.**

SupplyPilot does not simply accept that recommendation. The agent
investigates:

-   Current inventory
-   Demand forecast
-   Existing/open purchase orders
-   Supplier constraints and MOQ
-   Supplier capacity and lead time
-   Purchasing budget
-   Storage capacity
-   Replenishment/business rules
-   Procurement policies from the knowledge base

It then calculates a constrained replenishment quantity, produces an
explainable decision, and routes the procurement action through a human
approval gate.

After execution, the resulting purchase order is validated against the
intended action.

### Core workflow

``` text
System Recommendation
        |
        v
AI Investigation
        |
        +-- Inventory
        +-- Demand Forecast
        +-- Open POs
        +-- Supplier Constraints
        +-- Budget
        +-- Storage
        +-- Business Rules
        +-- Procurement Knowledge
        |
        v
Replenishment Calculation
        |
        v
Constraint Validation
        |
        v
AI Decision
  +-----+---------+
  |     |         |
Accept Modify   Reject
  |     |         |
  +-----+---------+
        |
        v
Human Approval
        |
        v
Purchase Order Execution
        |
        v
Post-action Validation
        |
   +----+----+
   |         |
Success   Mismatch
             |
             v
          Recovery
```

## Golden Demo

The primary demonstration is **PC-1001**, a hydraulic pump cartridge
purchasing case.

### Initial state

  Signal                              Value
  ----------------------------- -----------
  System recommendation           800 units
  Current inventory               300 units
  Expected demand                 700 units
  Existing inbound PO             200 units
  Supplier MOQ                    100 units
  Available budget                  \$4,000
  Additional storage capacity     600 units

### Agent outcome

SupplyPilot investigates the available evidence and changes the
recommendation:

``` text
800 units  ->  400 units
```

**Decision:** `MODIFY`\
**Confidence:** `92%`

The agent records the evidence and reasoning, then requests human
authorization before changing the purchase order.

### End-to-end result

``` text
800-unit recommendation
        |
        v
10 operational investigation tools completed
        |
        v
Recommendation modified to 400 units
        |
        v
Human approval
        |
        v
Purchase action executed
        |
        v
Purchase action validated
```

## Key Product Capabilities

### 1. Evidence-first investigation

The agent gathers operational evidence before making a purchasing
decision.

### 2. Deterministic constraint handling

Important procurement constraints are evaluated explicitly rather than
being left entirely to the language model.

Examples include:

-   Inventory coverage
-   Demand coverage
-   Existing inbound POs
-   Supplier MOQ
-   Supplier capacity
-   Budget
-   Storage capacity
-   Target-stock/replenishment policy

### 3. Explainable decisions

Each decision includes:

-   Original recommendation
-   AI-recommended quantity
-   Decision outcome
-   Confidence
-   Financial impact
-   Risk
-   Reason codes
-   Evidence used
-   Policy sources considered

### 4. Retrieval-augmented policy evidence

Procurement policies are retrieved from the knowledge base and
incorporated into the investigation.

### 5. Human-in-the-loop authorization

Procurement actions that require authorization are explicitly presented
for human review before execution.

### 6. Post-action validation

The system validates the resulting purchase order after execution rather
than assuming that a successful API call means the intended business
action occurred.

### 7. Auditability

Agent runs expose an operational evidence trail showing which tools were
used during the investigation.

## Architecture

``` text
+-----------------------------------------------+
|                 Next.js Web UI                |
|                                               |
| Dashboard | Cases | POs | Suppliers |        |
| Inventory | Agent Runs | Audit Logs | KB     |
+-------------------------------+---------------+
                                |
                                | REST API
                                v
+-----------------------------------------------+
|                  FastAPI API                  |
|                                               |
| Authentication | Cases | Procurement Actions |
| Validation | Audit/Event Persistence          |
+-------------------------------+---------------+
                                |
                                v
+-----------------------------------------------+
|              LangGraph Agent                 |
|                                               |
| Investigate -> Calculate -> Validate ->      |
| Decide -> Human Gate -> Execute -> Verify    |
+----------------+-------------+----------------+
                 |             |
                 v             v
          +-------------+  +---------+
          | PostgreSQL  |  |  Redis  |
          | + pgvector  |  |         |
          +-------------+  +---------+
                 |
                 v
          Procurement / policy
              knowledge
```

## Tech Stack

-   **Frontend:** Next.js, React, TypeScript
-   **Backend:** FastAPI, Python
-   **Agent orchestration:** LangGraph
-   **Database:** PostgreSQL
-   **Vector search:** pgvector
-   **Runtime/cache support:** Redis
-   **Containerization:** Docker Compose
-   **Database migrations:** Alembic

## Project Structure

``` text
SupplyPilot/
├── apps/
│   ├── api/                 # FastAPI backend and agent workflow
│   │   ├── app/
│   │   └── scripts/
│   └── web/                 # Next.js frontend
├── docker-compose.yml
├── .env.example
├── README.md
└── ...
```

## Running Locally

### Prerequisites

-   Docker Desktop
-   Git

The recommended setup is to run the complete stack through Docker
Compose.

### 1. Clone the repository

``` bash
git clone https://github.com/Kunal13Kashyap/supplypilot.git
cd supplypilot
```

### 2. Create the environment file

``` bash
cp .env.example .env
```

On Windows PowerShell:

``` powershell
Copy-Item .env.example .env
```

### 3. Start the application

``` bash
docker compose up --build
```

### 4. Open the web application

``` text
http://localhost:3000
```

The Docker Compose stack starts the web application, API, PostgreSQL,
and Redis services.

## Demo Credentials

The seeded demo environment currently provides:

``` text
Buyer
Email: buyer@procure.ai
Password: demo12345

Approver
Email: approver@procure.ai
Password: demo12345
```

> These are demo credentials for the seeded local environment.

## Golden Demo Walkthrough

1.  Sign in with the seeded buyer account.
2.  Open **Purchasing Cases**.
3.  Open the **golden case (PC-1001)**.
4.  Run **AI Investigation**.
5.  Review the evidence snapshot and operational evidence trail.
6.  Review the AI decision and constraint analysis.
7.  Review the proposed change from **800 -\> 400 units**.
8.  Approve and execute the procurement action.
9.  Confirm that the resulting purchase action is validated.
10. Review the resulting purchase order and audit evidence.

The important behavior to demonstrate is that the agent **investigates
before acting** and that the resulting action is **validated after
execution**.

## Example Investigation Trail

The golden case records operational tool calls including:

``` text
get_inventory
get_demand_forecast
get_open_purchase_orders
get_supplier_constraints
get_budget
get_storage_capacity
get_business_rules
search_knowledge_base
calculate_replenishment
validate_purchase_quantity
```

The UI exposes these calls as an evidence trail so the buyer can
understand what the agent actually checked.

## Decision Reasoning

For the golden case, the agent observes:

``` text
Inventory:       300
Inbound PO:      200
Expected demand: 700
```

Therefore:

``` text
300 + 200 = 500 units of coverage
700 - 500 = 200 units remaining demand
```

The agent then applies the replenishment policy and operational
constraints to determine the final proposed purchase quantity.

The resulting recommendation is:

``` text
Original:       800 units
AI proposal:    400 units
Decision:       MODIFY
```

The UI also surfaces the relevant constraint checks, policy evidence,
risk, confidence, and financial impact.

## Safety and Control Model

SupplyPilot separates **recommendation** from **authorization**.

The agent can investigate evidence and produce a proposed procurement
action, but the system can require a human to explicitly authorize the
resulting purchase action.

The execution flow is designed to be:

``` text
Investigate
    |
    v
Recommend
    |
    v
Validate proposal
    |
    v
Human authorization
    |
    v
Execute
    |
    v
Validate actual result
```

This prevents a model-generated recommendation from becoming an
unchecked purchasing action.

## Validation and Recovery

Post-action validation compares the intended procurement action with the
resulting operational state.

The system is designed to surface mismatches instead of treating an API
response as proof that the business operation succeeded.

This supports recovery-oriented behavior such as:

-   Detecting quantity mismatches
-   Surfacing validation exceptions
-   Preserving evidence
-   Allowing re-analysis or rejection
-   Keeping the operation auditable

## Development Checks

Frontend TypeScript can be checked with:

``` bash
cd apps/web
npm run typecheck
```

The project should return successfully with:

``` text
tsc --noEmit
```

## Environment

Use `.env.example` as the template for local configuration.

Do not commit real credentials or secrets.

The local demo can run using the project's seeded/demo configuration.

## Why SupplyPilot?

Traditional procurement workflows often treat an ERP recommendation as
an instruction.

SupplyPilot treats it as a **hypothesis that needs evidence**.

Instead of:

``` text
ERP says 800
      |
      v
Buy 800
```

SupplyPilot uses:

``` text
ERP says 800
      |
      v
Investigate
      |
      v
Check constraints
      |
      v
Explain decision
      |
      v
Get authorization
      |
      v
Execute
      |
      v
Verify
```

That distinction is the core idea behind the system.
