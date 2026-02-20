# Beispiele: Idempotente vs. riskante Projektionen

Konkrete Code-Beispiele für die Prüfpunkte des [Projection Idempotency Check](SKILL.md).

---

## 1. Direkte DB-Mutation vermeiden

**❌ Risiko – Service schreibt direkt ins Read-Model:**

```typescript
// applicationService.ts
async submitApplication(candidateId: string, jobId: string) {
  const application = await this.repo.save({ candidate_id: candidateId, job_id: jobId });
  await this.eventBus.publish(new ApplicationSubmitted(application.id, candidateId, jobId));

  // BAD: Direkte Aktualisierung eines Read-Models
  await this.db.namedQuery('updateApplicationCount', { candidateId });
}
```

**✅ Besser – Nur Event emittieren; Projektion aktualisiert:**

```typescript
// applicationService.ts
async submitApplication(candidateId: string, jobId: string) {
  const application = await this.repo.save({ candidate_id: candidateId, job_id: jobId });
  await this.eventBus.publish(new ApplicationSubmitted(application.id, candidateId, jobId));
  // Kein Schreibzugriff auf Read-Models.
}
```

```typescript
// applicationSummaryProjection.ts
async handle(event: ApplicationSubmitted) {
  await this.db.namedQuery('upsertApplicationSummary', {
    candidateId: event.payload.candidate_id,
    applicationCount: event.payload.newTotal, // aus Event, nicht COUNT+1
  });
}
```

---

## 2. Re-Run-Sicherheit: Zähler

**❌ Nicht re-run-sicher:**

```typescript
async handle(event: CandidateCreated) {
  await this.db.query(`
    UPDATE candidate_counts SET total = total + 1 WHERE scope = $1
  `, [event.payload.scope]);
}
```

Bei doppelter Zustellung oder Replay: `total` wird mehrfach erhöht.

**✅ Option A – Deduplizierung mit processed_events:**

```typescript
async handle(event: CandidateCreated) {
  const alreadyProcessed = await this.db.query(
    'SELECT 1 FROM processed_events WHERE event_id = $1 AND projection_name = $2',
    [event.event_id, 'candidate_counts']
  );
  if (alreadyProcessed.rows.length > 0) return;

  await this.db.query(`
    UPDATE candidate_counts SET total = total + 1 WHERE scope = $1
  `, [event.payload.scope]);

  await this.db.query(
    'INSERT INTO processed_events (event_id, projection_name) VALUES ($1, $2)',
    [event.event_id, 'candidate_counts']
  );
}
```

**✅ Option B – Absoluten Wert setzen (z. B. bei Rebuild):**

```typescript
async rebuild(scope: string) {
  const count = await this.eventStore.countEvents({ type: 'candidate.created', scope });
  await this.db.query(
    'INSERT INTO candidate_counts (scope, total, updated_at) VALUES ($1, $2, now()) ON CONFLICT (scope) DO UPDATE SET total = $2, updated_at = now()',
    [scope, count]
  );
}
```

---

## 3. Upsert statt reines INSERT

**❌ Re-Run erzeugt Duplikate:**

```typescript
async handle(event: JobPostingPublished) {
  await this.db.query(`
    INSERT INTO job_posting_summary (job_posting_id, title, published_at)
    VALUES ($1, $2, $3)
  `, [event.entity_id, event.payload.title, event.payload.published_at]);
}
```

**✅ Idempotent mit ON CONFLICT:**

```sql
-- Migration: Primary Key auf entity-Key
ALTER TABLE job_posting_summary ADD PRIMARY KEY (job_posting_id);
```

```typescript
async handle(event: JobPostingPublished) {
  await this.db.query(`
    INSERT INTO job_posting_summary (job_posting_id, title, published_at, updated_at)
    VALUES ($1, $2, $3, now())
    ON CONFLICT (job_posting_id) DO UPDATE SET
      title = EXCLUDED.title,
      published_at = EXCLUDED.published_at,
      updated_at = now()
  `, [event.entity_id, event.payload.title, event.payload.published_at]);
}
```

---

## 4. Keine Seiteneffekte im Handler

**❌ Seiteneffekt (E-Mail) in der Projektion:**

```typescript
async handle(event: OrderConfirmed) {
  await this.db.query('INSERT INTO order_summary ... ON CONFLICT ...');
  await this.emailService.send(event.payload.customer_email, 'OrderConfirmed', ...);
}
```

Bei Re-Run: Kunde erhält E-Mail mehrfach.

**✅ Projektion nur Read-Model; E-Mail in eigenem Consumer:**

```typescript
// orderSummaryProjection.ts
async handle(event: OrderConfirmed) {
  await this.db.query('INSERT INTO order_summary ... ON CONFLICT ...');
}

// orderConfirmationEmailConsumer.ts (separater Prozess, idempotent)
async handle(event: OrderConfirmed) {
  const sent = await this.db.query('SELECT 1 FROM sent_emails WHERE event_id = $1', [event.event_id]);
  if (sent.rows.length > 0) return;
  await this.emailService.send(...);
  await this.db.query('INSERT INTO sent_emails (event_id, ...) VALUES ($1, ...)', [event.event_id, ...]);
}
```

---

## 5. Minimales Schema für processed_events (Referenz)

```sql
CREATE TABLE processed_events (
  event_id        UUID NOT NULL,
  projection_name VARCHAR(255) NOT NULL,
  processed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (event_id, projection_name)
);
```

So kann dieselbe `event_id` von mehreren Projektionen verarbeitet werden, jede trägt sich einmal ein.
