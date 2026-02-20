---
name: projection-idempotency-check
description: Stellt sicher, dass Projektionen sicher aus dem Event-Log neu aufgebaut werden können. Prüft auf keine direkte DB-Mutation an Read-Models ohne Events, Re-Run-Sicherheit, korrekte Upsert-Logik und keine Seiteneffekte in Projektions-Handlern. Verwendet bei neuen oder geänderten Projektionen, Event-Handlern, Read-Models oder bei der Bewertung der Rebuild-Sicherheit. Liefert eine Idempotenz-Risikoanalyse und konkrete Refactor-Vorschläge.
---

# Projection Idempotency Check

Sicherstellen, dass Projektionen (Read-Models) jederzeit sicher aus dem Event-Log neu aufgebaut werden können – ohne direkte State-Mutation außerhalb von Events, mit Re-Run-Sicherheit, sauberer Upsert-Logik und ohne Seiteneffekte.

## Wann anwenden

- Neue oder geänderte Projektionen / Event-Handler / Read-Models
- Änderungen an Code, der aus Events in Tabellen/Views schreibt
- Bewertung der Rebuild-Sicherheit vor einem Full Replay
- Code-Review von Projektions-Logik

## Prüf-Checkliste

### 1. Keine direkte DB-State-Mutation ohne Events

- [ ] Read-Model-Tabellen/Views werden **nur** durch Projektions-Handler befüllt, die auf Events reagieren.
- [ ] Kein Service/Command schreibt direkt in Projektions-Tabellen (z. B. keine `INSERT/UPDATE` in `candidate_summary` außer im Projektions-Handler).
- [ ] Keine „Shortcuts“: State-Änderung immer über Event → Projektion, nie über direkten DB-Zugriff aus Business-Logik.

**Risiko:** Wenn irgendwo direkt in Projektions-Tabellen geschrieben wird, ist ein Rebuild aus dem Event-Log unvollständig oder inkonsistent.

### 2. Re-Run-Sicherheit

- [ ] Mehrfaches Verarbeiten derselben Events (gleiche `event_id`) führt zum **gleichen** Endzustand.
- [ ] Entweder: Deduplizierung (z. B. `processed_events` / `event_id`-Check vor Apply) oder strikte Upsert-Logik (siehe Punkt 3).
- [ ] Kein Zähler/Inkrement ohne Berücksichtigung von Duplikaten (z. B. `COUNT + 1` bei erneutem Event → falsch).

**Risiko:** Replay oder doppelte Event-Zustellung verfälscht die Projektion (Doppelzählung, doppelte Einträge).

### 3. Korrekte Upsert-Logik

- [ ] Projektionen schreiben nach **Entitäts-Key** (z. B. `entity_id`, `(aggregate_id, event_type)`), nicht nur append-only ohne Key.
- [ ] Bei gleichem Key: **UPSERT** (INSERT … ON CONFLICT UPDATE / MERGE), sodass erneutes Anwenden desselben oder neuerer Events den gleichen Zeilen-Endzustand erzeugt.
- [ ] Keine reinen INSERTs, die bei Re-Run Duplikate erzeugen (außer es ist bewusst ein Event-Log/Append-Only-Store).

**Risiko:** Re-Run erzeugt doppelte Zeilen oder veraltete Zustände.

### 4. Keine Seiteneffekte in Projektions-Handlern

- [ ] Handler führen **nur** lesende Zugriffe auf andere Bounded Contexts/APIs und Schreibzugriffe auf das **eigene** Read-Model aus.
- [ ] Keine E-Mails, keine externen API-Calls, keine weiteren Event-Publikationen, keine Logik die „weltverändernd“ ist – nur: Event lesen → Read-Model aktualisieren.
- [ ] Keine Abhängigkeit von Systemzeit oder nicht-deterministischen Werten für den geschriebenen State (oder explizit dokumentiert und bei Replay berücksichtigt).

**Risiko:** Rebuild führt zu doppelten E-Mails, doppelten API-Calls oder inkonsistentem State durch Nicht-Determinismus.

## Ausgabe-Format

Am Ende der Prüfung immer in diesem Format antworten:

```markdown
## Projection Idempotency Check

**Ergebnis:** LOW RISK | MEDIUM RISK | HIGH RISK

### Risikoanalyse
- Direkte DB-Mutation (ohne Events): ✅ unkritisch / ⚠️ eingeschränkt / ❌ Risiko
- Re-Run-Sicherheit: ✅ / ⚠️ / ❌
- Upsert-Logik: ✅ / ⚠️ / ❌
- Keine Seiteneffekte: ✅ / ⚠️ / ❌

### Kurzbegründung
[1–3 Sätze zu den Hauptrisiken]

### Refactor-Vorschläge (bei MEDIUM/HIGH RISK)
- [Konkrete, umsetzbare Schritte – Datei/Stelle, gewünschtes Verhalten, ggf. Code-Skizze]
```

Refactor-Vorschläge müssen **konkret** sein: betroffene Datei/Stelle, gewünschtes Verhalten, ggf. Beispiel (Deduplizierung, Upsert-Schema, Auslagerung von Seiteneffekten).

## Beispiele für Refactor-Vorschläge

**Direkte DB-Mutation:**
- „In `ApplicationService.submit()` wird `application_summary` direkt aktualisiert. Entfernen; stattdessen nur Event emittieren und in `ApplicationSummaryProjection` aus dem Event die Zeile schreiben/upserten.“

**Re-Run unsicher (Zähler):**
- „`CandidateCountProjection` macht `UPDATE counts SET total = total + 1`. Bei Re-Run wird doppelt gezählt. Stattdessen: aus Events alle `CandidateCreated` für den Scope zählen und `total` setzen (ersetzen, nicht inkrementieren), oder `processed_events` mit `event_id` führen und nur neue Events anwenden.“

**Falsche Upsert-Logik:**
- „`JobPostingProjection` nutzt nur `INSERT`. Bei erneutem Replay entstehen Duplikate. Primary Key auf `(job_posting_id)` legen und `INSERT ... ON CONFLICT (job_posting_id) DO UPDATE SET ...` verwenden, abgeleitet aus `entity_id` / Payload.“

**Seiteneffekt im Handler:**
- „In `OrderConfirmedProjection` wird eine E-Mail versendet. Seiteneffekt aus der Projektion entfernen; E-Mail-Versand in einen separaten Prozess legen (z. B. eigener Consumer), der einmal pro `event_id` arbeitet (idempotent).“

## Kurz-Referenz: Idempotente Projektion

- Ein Event → eine deterministische Aktualisierung des Read-Models.
- Schlüssel = Entitäts-Key (z. B. `entity_id`); Schreibart = Upsert.
- Keine Seiteneffekte; keine direkte Schreibzugriffe auf das Read-Model außerhalb des Handlers.
- Re-Run (Replay) oder doppelte Zustellung führt zum gleichen Endzustand.

## Weitere Ressourcen

- Detaillierte Patterns (processed_events, Upsert-SQL, Zähler, Rebuild): [reference.md](reference.md)
- Code-Beispiele (richtig vs. falsch): [examples.md](examples.md)
