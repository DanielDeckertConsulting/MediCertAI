---
name: db-migration-safety-check
description: Prüft Datenbank-Migrationen auf Rückwärtskompatibilität, Reversibilität, Datenverlust- und Lock-Risiko für Produktion. Verwendet bei Migrationsdateien, Schema-Änderungen (ALTER/CREATE/DROP), Rollback-Planung, „migration safety“, „Schema sicher“, „DB-Migration prüfen“, Datenverlust-Risiko, Lock-Risiko, backward compatibility oder wenn der Nutzer eine Sicherheitsprüfung für Migrationen anfordert. Liefert Safe/Unsafe mit konkreten Fix-Vorschlägen.
---

# DB-Migration-Safety-Check

Stelle sicher, dass Schema-Änderungen sicher für Produktion sind: rückwärtskompatibel, reversibel, ohne Datenverlust und ohne unnötige Locks.

## Wann anwenden (Trigger)

Skill anwenden, wenn einer der folgenden Fälle zutrifft:

- **Dateien/Kontext:** Neue oder geänderte Migrationsdateien (SQL, ORM wie TypeORM, Prisma, Flyway, Liquibase, etc.)
- **Schema-Operationen:** Geplante oder geschriebene `ALTER TABLE`, `CREATE TABLE`, `DROP TABLE`/`DROP COLUMN`, `RENAME COLUMN`, Typ- oder Constraint-Änderungen
- **Stichwörter des Nutzers:** „migration safety“, „Migration prüfen“, „Schema sicher“, „DB-Migration check“, „Rollback“, „backward compatibility“, „Datenverlust vermeiden“, „Lock-Risiko“, „Produktion sicher“

**Regel:** Bei Unsicherheit, ob der Nutzer eine Sicherheitsprüfung will → Skill anwenden und kurze Prüfung durchführen.

## Prüf-Checkliste

**Bewertung:** Sobald eine Prüfung mit ❌ bewertet wird → Gesamtergebnis **Unsafe**. Nur wenn alle vier Prüfungen ✅ sind → **Safe**.

### 1. Rückwärtskompatibilität

- [ ] **Spalten entfernen:** Alte App-Versionen dürfen keine entfernten Spalten mehr lesen/schreiben. Entweder: Spalte erst als „deprecated“ markieren, neue Version ausrollen, dann Spalte in späterer Migration entfernen – oder Feature-Flag/Version-Check.
- [ ] **Spalten umbenennen:** Kein direktes `RENAME COLUMN`, wenn alte und neue Version gleichzeitig laufen. Stattdessen: neue Spalte anlegen, Daten kopieren, App umstellen, alte Spalte in Folgemigration entfernen.
- [ ] **Typ-Änderungen:** `VARCHAR`→`TEXT` oder Verlängerung ist meist unkritisch; Verkürzung oder Änderung des Typs (z.B. `INTEGER`→`UUID`) kann Laufzeitfehler auslösen. Explizit prüfen, ob alte App den alten Typ noch erwartet.
- [ ] **NOT NULL hinzufügen:** Nur sicher, wenn Spalte bereits einen DEFAULT hat oder keine NULL-Werte existieren. Sonst: zuerst NULL-Werte bereinigen oder DEFAULT setzen, dann NOT NULL.
- [ ] **Neue Tabellen/Indizes:** Nur neue Objekte hinzugefügt (keine Änderung an bestehenden Spalten, die alte App nutzt) → in der Regel ✅.

### 2. Reversibilität (Rollback)

- [ ] **Down-Migration vorhanden:** Jede Migration hat eine definierte Rücknahme („down“, „rollback“, `down`-Methode), die den Zustand vor der Migration wiederherstellt. Fehlt die Down-Logik → ❌.
- [ ] **Down ist wirklich umkehrbar:** z.B. bei „Spalte hinzugefügt“ → Down entfernt die Spalte; bei „Spalte gelöscht“ → Down kann die Spalte nur wieder anlegen, **nicht** die alten Daten zurückbringen (Datenverlust bei Rollback akzeptabel dokumentieren).
- [ ] **Reihenfolge:** Rollback in umgekehrter Reihenfolge der Migrations; Abhängigkeiten (Foreign Keys, Tabellen) werden in Down in korrekter Reihenfolge aufgelöst (z.B. zuerst FK/Child-Tabellen, dann Parent).

### 3. Datenverlust-Risiko

- [ ] **DROP TABLE / DROP COLUMN:** Immer prüfen, ob Daten noch benötigt werden. Wenn ja: Backup, Archivierung oder Soft-Delete vor dem physischen Löschen. Unkommentiertes DROP ohne dokumentierte Absicht → ❌.
- [ ] **Überschreiben von Daten:** UPDATE ohne WHERE oder massenhaftes Überschreiben nur mit expliziter Bestätigung und ggf. Backup.
- [ ] **Typ- oder Format-Änderung:** Konvertierung muss alle bestehenden Zeilen korrekt abbilden; fehlgeschlagene Zeilen = potenzieller Datenverlust oder fehlgeschlagene Migration.

### 4. Lock-Risiko für Produktion

- [ ] **Lange haltende Locks:** `ALTER TABLE ... ADD COLUMN` mit DEFAULT kann in einigen DBs (z.B. ältere PostgreSQL-Versionen) einen Full-Table-Lock erzeugen. Prüfen: Nutzt die DB „instant“/online DDL oder blockiert die Tabelle?
- [ ] **Große Tabellen:** Bei Millionen Zeilen: Lock-Dauer und Zeitfenster (Wartungsfenster) berücksichtigen. Optionen: Online-Migration, Shadow-Spalte + Backfill, Staging-Migration mit Switch.
- [ ] **Index-Erstellung:** `CREATE INDEX CONCURRENTLY` (PostgreSQL) nutzen, um Schreib-Locks zu vermeiden; in manchen Systemen als separate Migration ohne Transaktion. `CREATE INDEX` ohne CONCURRENTLY auf großer Tabelle → potenziell ❌.
- [ ] **Foreign Keys / Constraints:** Hinzufügen mit `NOT VALID` + später `VALIDATE` (PostgreSQL) kann Lock-Zeit reduzieren.

## Ausgabe-Format

Am Ende der Prüfung immer in diesem Format antworten:

```markdown
## DB-Migration-Safety-Check

**Ergebnis:** Safe | Unsafe

### Prüfungen
- Rückwärtskompatibilität: ✅ / ❌
- Reversibilität (Rollback): ✅ / ❌
- Datenverlust-Risiko: ✅ / ❌
- Lock-Risiko Produktion: ✅ / ❌

### Erforderliche Anpassungen (nur bei Unsafe)
- [Konkrete, umsetzbare Schritte pro fehlgeschlagener Prüfung]
```

Anpassungen müssen **konkret** sein: betroffene Migration/Zeile, vorgeschlagene Änderung (z.B. „Down-Migration ergänzen“, „ADD COLUMN ohne DEFAULT oder mit DEFAULT in separatem Schritt“). Pro fehlgeschlagener Prüfung mindestens einen Fix-Vorschlag nennen.

## Beispiele für Fix-Vorschläge

**Keine Down-Migration:**
- „In `20250214_add_phone_to_candidates.sql` fehlt die Rollback-Logik. Ergänze z.B. `-- down: ALTER TABLE candidates DROP COLUMN phone;` oder entsprechende Down-Datei.“

**RENAME ohne Kompatibilität:**
- „`RENAME COLUMN created_at TO created_at_utc` bricht laufende Instanzen. Vorgehen: Neue Spalte `created_at_utc` anlegen, Backfill, App auf neue Spalte umstellen, alte Spalte in Folgemigration entfernen.“

**Lock-Risiko:**
- „`ALTER TABLE events ADD COLUMN payload_checksum VARCHAR(64) DEFAULT NULL` kann bei großer Tabelle lange blockieren. Option: Spalte ohne DEFAULT hinzufügen, in separatem Schritt per Batch-UPDATE füllen; oder PostgreSQL 11+ nutzen (ADD COLUMN mit DEFAULT ist dann oft instant).“

**Datenverlust:**
- „`DROP COLUMN legacy_id` löscht Daten endgültig. Vorher prüfen, ob kein Service mehr `legacy_id` nutzt; optional Archiv in Tabelle `candidates_legacy_ids` exportieren, dann Spalte droppen.“

## Projekt-Konventionen (PostgreSQL)

- Tabellen- und Spaltennamen: **snake_case** (`created_at`, `user_id`, `is_verified`).
- Standardfelder `created_at` und `updated_at` in Tabellen beibehalten bzw. bei neuen Tabellen anlegen.
- Booleans mit `is_`, `has_`, `can_`; Typ `BOOLEAN` mit `DEFAULT TRUE`/`FALSE`.
- `TEXT` oder `VARCHAR(n)` für Strings, `UUID` für IDs – keine unscharfen Typen für Fremdschlüssel.

Diese Konventionen bei neuen oder geänderten Schema-Objekten in der Migration einhalten.
