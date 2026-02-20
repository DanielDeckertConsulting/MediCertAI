# schema-upgrade

Dieser Command ist verfügbar im Chat mit `#schema_upgrade` bzw. `/schema-update`.

---

You are the **EVENT SCHEMA UPGRADE ORCHESTRATOR** for the EasyHeadHunter project.

## Mission

Introduce a **versioned event schema upgrade mechanism** that allows old events to be read and projected safely. Upgrades happen at **read time** via upcasters; the event_store remains immutable.

---

## User Input

- **Change description:** What fields change / add / remove (inkl. payload-Struktur falls betroffen).
- **Target schema_version:** Integer (z. B. 2).
- **Backward compatibility requirement:** `STRICT` (alle alten Events müssen exakt nach neuem Schema transformierbar sein) oder `BEST_EFFORT` (Defaults/Platzhalter erlaubt, wo Daten fehlen).

---

## Hard Rules

1. **event_store is immutable:** Do NOT rewrite historical events in MVP.
2. **Upgrades at read time:** Via upcasters (event schema transformers); beim Lesen/Replay wird von gespeicherter `schema_version` auf aktuelle Version hochtransformiert.
3. **Projections rebuildable:** Projektionen müssen mit hochtransformierten Events (aktuelle Schema-Version) idempotent neu aufgebaut werden können.
4. **Document the schema evolution rule:** Schema-Evolution-Policy festhalten (z. B. in `docs/events.md` oder `docs/schema_evolution.md`).

---

## Deliverables

1. **Schema evolution policy (rules)**  
   - Wann wird `schema_version` erhöht?  
   - Nur additive Änderungen vs. Breaking Changes.  
   - Wo dokumentiert (shared/events/schema.json, docs).

2. **Upcaster design**  
   - Funktion `upcast(event) -> event_vN` (von gespeicherter Version auf Zielversion).  
   - **One upcaster per version step** (v1→v2, v2→v3), verkettet beim Lesen.  
   - Klare Signatur: Input = rohes Event (wie aus DB), Output = Event in aktueller Schema-Version (für Projektoren).

3. **Storage**  
   - **event_store** behält die **originale** `schema_version` pro Event (keine Überschreibung).  
   - **Application** nutzt im Code immer die **aktuelle** Schema-Version; Lesepfad wendet Upcaster-Kette an.

4. **Implementation plan**  
   - **shared/events/schema.json** aktualisieren (z. B. neue optionale Felder, Hinweis auf unterstützte Versionen).  
   - **Backend Upcaster-Modul** (z. B. `backend/app/domain/events/upcasters.py` + Registry/Kette).  
   - **Tests**, die beweisen, dass alte Events (z. B. schema_version=1) nach Upcast noch korrekt projiziert werden.

5. **Acceptance criteria + test plan**  
   - Gegeben Event mit schema_version N, wenn Upcaster-Kette angewendet wird, dann ist Ergebnis Event mit schema_version = current.  
   - Gegeben Projektor P, wenn Replay mit upgecasteten Events, dann gleiches Ergebnis wie mit nativ aktuellen Events (wo anwendbar).  
   - Testplan: Unit-Tests pro Upcaster, mind. ein Integrationstest (alter Event → Upcast → Projektor).

---

## Output format

Liefer die folgenden Abschnitte und **ende mit: READY_FOR_SCHEMA_UPGRADE**.

1. **Proposed schema changes**  
   - Diff-artige Beschreibung (welche Felder neu, geändert, entfernt; Envelope vs. payload).

2. **Upcaster examples**  
   - Vorher/Nachher-Payload (oder ganzes Event) pro Versionsschritt (z. B. v1→v2).

3. **Files to touch**  
   - Konkret: z. B. `shared/events/schema.json`, `backend/app/domain/events/schemas.py`, `backend/app/domain/events/upcasters.py`, `backend/app/domain/events/event_store.py` (Lesepfad), `docs/events.md` oder `docs/schema_evolution.md`, Tests unter `backend/tests/`.

4. **Risks + mitigations**  
   - Risiko (z. B. Datenverlust bei BEST_EFFORT, Reihenfolge der Upcaster).  
   - Mitigation (Tests, strikte Ein-Schritt-Upcaster, Dokumentation).

---

## Projekt-Kontext (EasyHeadHunter)

- Kanonisches Event-Schema: **`shared/events/schema.json`** (Envelope mit `event_id`, `ts`, `actor`, `entity_type`, `entity_id`, `event_type`, `payload`, `source`, `schema_version`).
- Backend-Modelle: **`backend/app/domain/events/schemas.py`** (`DomainEventSchema`, `EventCreate`); **`backend/app/domain/events/event_store.py`** (PostgresEventStore liest/schreibt mit `schema_version`).
- Tabelle **`event_store`** enthält Spalte **`schema_version`** (Migration `0001_create_event_store.py`); wird beim Append gesetzt, beim Lesen nicht verändert.
- Projektoren: **`backend/app/domain/projections/`**; Rebuild: Command **rebuild-projection** (Events chronologisch lesen, an Projektoren geben).  
- Upcaster-Einbindung: Beim **Lesen** aus dem Event-Store (z. B. in `list_events` oder im Rebuild-Script) Events durch Upcaster-Kette jagen, bevor sie an Projektoren oder API gehen.

---

**Output:** Alle genannten Deliverables ausarbeiten und die Antwort mit **READY_FOR_SCHEMA_UPGRADE** beenden.
