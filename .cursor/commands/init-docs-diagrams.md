#init_docs_diagrams

You are the DOCUMENTATION INFRASTRUCTURE ENGINEER for the EasyHeadHunter project.

Mission:
Initialize a reproducible diagram structure for architecture, flows, and event visualization.
All diagrams must use Mermaid syntax (preferred) and be version-controlled.

Tech Context:
- Monorepo
- Event-Log-first backend
- Next.js frontend
- Azure (optional, future-ready)
- Mermaid diagrams only (no images, no screenshots)

========================================================
TASK
========================================================

Create the following folder structure:

/docs
  /diagrams
    /c4
      c4-context.mmd
      c4-container.mmd
    /flows
      seq-golden-path.mmd
      eventflow-golden-path.mmd
    /deployment
      deploy-azure.mmd
    /data
      projection-structure.mmd

Also update:
- /docs/architecture.md
- /docs/events.md

========================================================
DIAGRAM TEMPLATE REQUIREMENTS
========================================================

All diagrams must:
- Be syntactically valid Mermaid
- Contain realistic placeholders aligned with our architecture
- Avoid PII
- Be clean and minimal
- Be editable and reusable

========================================================
CONTENT SPECIFICATIONS
========================================================

1️⃣ c4-context.mmd
- System boundary: EasyHeadHunter
- External actors: User, Admin
- Optional external systems placeholder
- Show frontend + backend as black boxes

2️⃣ c4-container.mmd
Show:
- Next.js Frontend
- FastAPI Backend
- Event Store (Postgres)
- Projection Tables
- Optional Worker
- Optional Azure resources (Key Vault, App Insights placeholder)

3️⃣ seq-golden-path.mmd
Sequence diagram:
User → Frontend → Backend → Event Store → Projector → Read Model → Frontend refresh

Include:
- lead.created
- projection update
- UI refresh

4️⃣ eventflow-golden-path.mmd
Graph diagram showing:
lead.created
call.started
call.ended
lead.status.updated

Show event order visually.

5️⃣ deploy-azure.mmd
Simple deployment sketch:
User → Azure Front Door (placeholder)
→ App Service
→ Azure Database for PostgreSQL
→ Key Vault
→ Application Insights

Keep minimal and editable.

6️⃣ projection-structure.mmd
Data structure visualization:
- event_store table
- example projection table
- show relationship arrows

========================================================
UPDATE DOCUMENTATION FILES
========================================================

Update /docs/architecture.md:
- Embed links to C4 diagrams
- Add short explanation of diagram types

Update /docs/events.md:
- Link to eventflow diagram
- Add short description of event lifecycle

========================================================
OUTPUT FORMAT
========================================================

Provide:
1) List of created files with paths
2) Full Mermaid content of each file
3) Short explanation of structure

End with:
DOCS_DIAGRAMS_INITIALIZED
