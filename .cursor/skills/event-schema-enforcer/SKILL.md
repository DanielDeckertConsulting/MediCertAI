---
name: event-schema-enforcer
description: Prüft, ob jede Business-Aktion ein wohlgeformtes Domain-Event emittiert. Verwendet bei neuen Schreiboperationen, Änderungen an Business-Logik die State ändert, sowie bei neuen oder geänderten Projektionen. Prüft Event-Emission, Pflichtfelder (event_id, timestamp, actor, entity_type, entity_id, event_type, payload, source), Schema-Versionierung und Idempotenz von Projektionen. Liefert PASS/FAIL mit konkreten Fix-Vorschlägen.
---

# Event-Schema-Enforcer

Stelle sicher, dass jede Business-Aktion ein unveränderliches, wohlstrukturiertes Domain-Event emittiert und Projektionen idempotent sind.

## Wann anwenden

- Neue Schreiboperationen (Commands, Mutations, Services die State ändern)
- Business-Logik, die persistenten State modifiziert
- Neue oder geänderte Projektionen / Event-Handler / Read-Models

## Prüf-Checkliste

### 1. Event-Emission

- [ ] Jede Business-Aktion, die State ändert, emittiert **mindestens ein** unveränderliches Event.
- [ ] Events werden **nach** der erfolgreichen State-Änderung emittiert (oder als Teil einer transaktionalen Outbox).
- [ ] Kein State-Change ohne zugehöriges Event.

### 2. Event-Schema (Pflichtfelder)

Jedes Event muss folgende Felder enthalten:

| Feld | Bedeutung |
|------|-----------|
| `event_id` | Eindeutige ID des Events (z. B. UUID) |
| `timestamp` | Zeitpunkt der Aktion (ISO 8601 oder Unix) |
| `actor` | Wer hat die Aktion ausgelöst (User-ID, System, Service) |
| `entity_type` | Typ der betroffenen Entität (z. B. `candidate`, `job_posting`) |
| `entity_id` | ID der betroffenen Entität |
| `event_type` | Art des Events (z. B. `candidate.created`, `application.submitted`) |
| `payload` | Nutzdaten der Aktion (strukturiert, nur relevante Felder) |
| `source` | Herkunft (Service-Name, Bounded Context, Stream) |

- [ ] Alle acht Felder sind im Event-Schema vorhanden und werden befüllt.
- [ ] Keine optionalen Pflichtfelder; fehlt eines → FAIL.

### 3. Schema-Versionierung

- [ ] Events sind versionierbar (z. B. `schema_version`, `event_version` oder im `event_type` wie `v2.candidate.created`).
- [ ] Änderungen am Payload/Schema führen zu neuer Version; alte Consumer können weiterhin alte Version lesen oder migrieren.

### 4. Idempotenz der Projektionen

- [ ] Projektionen/Event-Handler sind idempotent: mehrfache Verarbeitung desselben Events (gleiche `event_id`) führt zum gleichen Ergebnis.
- [ ] Typische Umsetzung: `event_id` in Processed-Events-Tabelle oder Deduplizierung vor Apply.

## Ausgabe-Format

Am Ende der Prüfung immer in diesem Format antworten:

```markdown
## Event-Schema-Enforcer

**Ergebnis:** PASS | FAIL

### Prüfungen
- Event-Emission: ✅ / ❌
- Event-Schema (Pflichtfelder): ✅ / ❌
- Schema-Versionierung: ✅ / ❌
- Idempotenz Projektionen: ✅ / ❌ (oder „nicht anwendbar“)

### Fix-Vorschläge (nur bei FAIL)
- [Konkrete, umsetzbare Vorschläge pro fehlgeschlagener Prüfung]
```

Fix-Vorschläge müssen **konkret** sein: betroffene Datei/Stelle, fehlendes Feld oder fehlende Logik, Beispiel-Code oder Schema-Änderung.

## Beispiele für Fix-Vorschläge

**Fehlendes Pflichtfeld:**
- „In `CandidateCreatedEvent` fehlt das Pflichtfeld `source`. Ergänze z. B. `source: 'recruitment-api'` bzw. Konfigurationswert.“

**Kein Event bei State-Change:**
- „In `ApplicationService.submit()` wird die Bewerbung persistiert, aber kein Event emittiert. Nach dem Speichern `eventBus.publish(new ApplicationSubmitted(...))` aufrufen und alle Pflichtfelder befüllen.“

**Projektion nicht idempotent:**
- „`CandidateCountProjection` verarbeitet `CandidateCreated` ohne Deduplizierung. Vor dem Apply prüfen, ob `event_id` bereits in `processed_events` vorkommt; sonst ignorieren oder überschreiben.“

## Kurz-Referenz: Minimal-Event (Struktur)

```json
{
  "event_id": "uuid",
  "timestamp": "2025-02-14T12:00:00Z",
  "actor": "user_id oder system",
  "entity_type": "candidate",
  "entity_id": "entity-uuid",
  "event_type": "candidate.created",
  "payload": { },
  "source": "recruitment-api"
}
```

Schema-Version optional als zusätzliches Feld oder in `event_type` (z. B. `v1.candidate.created`).
