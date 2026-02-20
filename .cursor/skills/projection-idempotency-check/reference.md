# Referenz: Idempotente Projektionen

Detaillierte Patterns für Re-Run-Sicherheit und saubere Upsert-Logik. Siehe [SKILL.md](SKILL.md) für die Prüf-Checkliste.

---

## 1. Deduplizierung über processed_events

Um mehrfache Verarbeitung desselben Events zu verhindern, eine Tabelle pro Projektion (oder eine zentrale mit `projection_name`):

```sql
CREATE TABLE processed_events (
  event_id     UUID PRIMARY KEY,
  projection_name VARCHAR(255) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Optional: Index für "welche Events hat diese Projektion schon gesehen"
CREATE INDEX idx_processed_events_projection ON processed_events (projection_name);
```

**Ablauf im Handler:**

1. Event empfangen (z. B. `event_id`, `entity_id`, `payload`).
2. `SELECT 1 FROM processed_events WHERE event_id = $1 AND projection_name = $2`.
3. Wenn Zeile existiert → Event überspringen (idempotent).
4. Sonst: Read-Model aktualisieren (Upsert), danach `INSERT INTO processed_events (event_id, projection_name)`.

Wichtig: Schritt 4 in derselben Transaktion wie die Read-Model-Aktualisierung ausführen, sonst kann bei Crash ein Event doppelt angewendet werden.

---

## 2. Alternativ: Idempotenz nur durch Upsert (ohne processed_events)

Wenn das Read-Model **pro Entität genau eine Zeile** hat und alle Updates über den Entitäts-Key laufen, reicht Upsert – gleiches Event nochmal anwenden überschreibt mit denselben Werten.

- Primärschlüssel = z. B. `entity_id` (oder `(aggregate_id, projection_scope)`).
- Jeder Handler führt nur **UPDATE/INSERT nach diesem Key** aus (kein blindes INSERT).
- Keine Zähler wie `SET count = count + 1`; stattdessen Wert aus Event/Payload setzen oder aus Events neu berechnen.

Dann ist Re-Run sicher, ohne eine separate processed_events-Tabelle.

---

## 3. Upsert in PostgreSQL

**Variante A: INSERT ... ON CONFLICT DO UPDATE**

```sql
INSERT INTO candidate_summary (
  candidate_id,
  full_name,
  application_count,
  last_activity_at,
  updated_at
) VALUES (
  $1, $2, $3, $4, now()
)
ON CONFLICT (candidate_id) DO UPDATE SET
  full_name         = EXCLUDED.full_name,
  application_count = EXCLUDED.application_count,
  last_activity_at  = EXCLUDED.last_activity_at,
  updated_at        = now();
```

Der Primärschlüssel (hier `candidate_id`) muss dem Entitäts-Key entsprechen (z. B. `entity_id` aus dem Event).

**Variante B: MERGE (PostgreSQL 15+)**

```sql
MERGE INTO job_posting_summary AS t
USING (SELECT $1::UUID AS job_posting_id, $2::TEXT AS title, $3::TIMESTAMPTZ AS published_at) AS s
ON t.job_posting_id = s.job_posting_id
WHEN MATCHED THEN UPDATE SET
  title       = s.title,
  published_at = s.published_at,
  updated_at  = now()
WHEN NOT MATCHED THEN INSERT (job_posting_id, title, published_at, created_at, updated_at)
  VALUES (s.job_posting_id, s.title, s.published_at, now(), now());
```

---

## 4. Zähler / Aggregationen idempotent machen

**Problem:** `UPDATE counts SET total = total + 1` ist bei Re-Run falsch (Doppelzählung).

**Lösung 1 – Ersetzen statt Inkrement:**  
Read-Model speichert den **absoluten** Wert. Bei Rebuild: alle relevanten Events laden, neu berechnen, einmal schreiben (z. B. `UPDATE counts SET total = $computed_total WHERE scope = $1`).

**Lösung 2 – Deduplizierung:**  
Nur Events anwenden, die noch nicht in `processed_events` stehen; dann ist `total = total + 1` pro Event genau einmal korrekt.

**Lösung 3 – Event-gebundene Zeilen:**  
Statt einer Zeile „total = 5“ eine Tabelle „ein Event = eine Zeile“ (z. B. `candidate_created_events(event_id PRIMARY KEY, candidate_id, created_at)`). Die „Summe“ ist dann `COUNT(*)` oder wird in einer Materialized View berechnet. Re-Run = Upsert nach `event_id`, also idempotent.

---

## 5. Keine Seiteneffekte im Handler

| Erlaubt im Projektions-Handler | Nicht erlaubt |
|--------------------------------|----------------|
| Event lesen | E-Mail versenden |
| DB lesen (eigenes Read-Model oder Event-Store) | Externe API aufrufen |
| In eigenes Read-Model schreiben (Upsert) | Weitere Events publizieren |
| In processed_events schreiben | Andere Read-Models anderer Bounded Contexts schreiben |
| Logging (ohne sensible Daten) | Systemzeit für Business-Logik (außer dokumentiert) |

Seiteneffekte (E-Mail, API, neues Event) in einen **eigenen Consumer** auslagern, der einmal pro `event_id` arbeitet (idempotent), z. B. über eigene „processed“-Tabelle oder idempotente API.

---

## 6. Rebuild aus dem Event-Log

- Events in fester Reihenfolge lesen (z. B. nach `timestamp` oder `sequence`).
- Projektions-Tabellen vor Rebuild leeren (oder gezielt pro Projektion truncate).
- `processed_events` für diese Projektion leeren (falls verwendet).
- Alle Events erneut an die Projektions-Handler geben.
- Am Ende sollte der Read-Model-Zustand identisch mit einem Single-Pass sein.

Wenn irgendwo **direkt** in Projektions-Tabellen geschrieben wird (ohne Event), fehlen diese Änderungen beim Rebuild → Zustand inkonsistent. Daher: alle Schreibzugriffe auf Read-Models nur in Projektions-Handlern, getrieben durch Events.
