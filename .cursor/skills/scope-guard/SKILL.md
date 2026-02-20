---
name: scope-guard
description: Prevents scope creep inside a ticket. Checks whether changed files and features match the ticket scope, and whether the PR stays within single-ticket boundaries. Use when reviewing a PR against a ticket, when checking if changes fit the ticket, or when the user asks for scope validation or "scope creep".
---

# Scope Guard

Verhindert Scope Creep: Prüft, ob Änderungen (Dateien + Funktionalität) zum Ticket passen und ob die PR die Ein-Ticket-Grenze einhält.

## Wann anwenden

- PR oder Branch wird gegen ein Ticket geprüft
- Nutzer fragt nach Scope-Validierung oder „Scope Creep“
- Vor Merge-Check: „Passt alles zu diesem einen Ticket?“

### Trigger / Stichwörter

Skill anwenden, wenn der Nutzer z. B. sagt:

- „Scope prüfen“, „Scope Guard“, „Scope-Validierung“
- „Passt die PR zum Ticket?“, „Gehört das alles zu diesem Ticket?“
- „Scope Creep prüfen“, „Ist das noch im Scope?“
- „Sind da fremde Dateien / Zusatz-Features drin?“
- „Sollten wir das aufteilen?“ (im Kontext einer PR)

## Voraussetzungen

- **Ticket-Kontext**: Ticket-ID, Titel, Beschreibung und/oder Akzeptanzkriterien (Given/When/Then)
- **Änderungs-Kontext**: Geänderte Dateien (Pfade) und optional kurze Beschreibung der Änderungen oder Diff-Zusammenfassung

Ohne Ticket- und Änderungs-Kontext die fehlenden Infos vom Nutzer einfordern.

## Prüfungen (der Reihe nach)

### 1. Unrelated Files (fremde Dateien)

- Jede geänderte Datei muss **nachvollziehbar dem Ticket zugeordnet** werden können (Feature, Bugfix, Refactor für dieses Ticket).
- **Verletzung**: Dateien, die weder im Ticket erwähnt noch logisch für die Erfüllung der AC nötig sind (z. B. Formatierung in anderen Modulen, Änderungen an unabhängigen Features).

### 2. Additional Features (Zusatz-Features)

- Alle sichtbaren Änderungen müssen den **Akzeptanzkriterien oder der Ticket-Beschreibung** entsprechen.
- **Verletzung**: Neue Funktionen, UI-Elemente oder Verhaltensänderungen, die in keinem AC und keiner Beschreibung des Tickets vorkommen („hab ich gleich mit gemacht“).

### 3. Single-Ticket Boundary (Ein-Ticket-Grenze)

- Die PR löst **genau ein Ticket** ab. Keine Kombination mehrerer Tickets in einer PR (außer explizit so vereinbart).
- **Verletzung**: Mehrere inhaltlich getrennte Themen/Fixes/Features in einer PR, die unterschiedlichen Tickets zugeordnet werden müssten.

## Ausgabe-Format (immer verwenden)

Am Ende der Prüfung immer in diesem Format antworten:

```markdown
## Scope Guard – [Ticket-ID oder -Titel]

### Scope Violation: [YES | NO]

### Prüfergebnis

| Prüfung              | Status  | Kurzbegründung |
|----------------------|---------|----------------|
| Unrelated Files      | OK / VIOLATION | … |
| Additional Features  | OK / VIOLATION | … |
| Single-Ticket Boundary | OK / VIOLATION | … |

### Details (nur bei VIOLATION)

- **Fremde/unklare Dateien**: [Liste oder „keine“]
- **Zusatz-Features**: [Kurzbeschreibung oder „keine“]
- **Grenzüberschreitung**: [Erläuterung oder „keine“]

### Suggested Split (nur wenn nötig)

[Falls Scope Violation: YES]
- **Option A**: [Was in dieser PR bleiben sollte – nur ticket-relevante Änderungen]
- **Option B**: [Was in separates Ticket/PR auslagern – mit kurzer Begründung]

[Falls Scope Violation: NO]
- Kein Split nötig.
```

## Beispiel-Ausgaben

### Beispiel 1: Scope Violation NO (sauber im Scope)

**Kontext:** Ticket EHH-42 „Neues Feld ‚Kündigungsgrund‘ im Lead-Formular“. Geändert: Lead-Formular-Komponente, Lead-Schema, API-Validierung, ein Unit-Test.

```markdown
## Scope Guard – EHH-42 (Kündigungsgrund im Lead-Formular)

### Scope Violation: NO

### Prüfergebnis

| Prüfung                | Status | Kurzbegründung |
|------------------------|--------|----------------|
| Unrelated Files        | OK     | Alle Dateien dienen dem neuen Feld (Formular, Schema, API, Test). |
| Additional Features    | OK     | Nur Kündigungsgrund-Feld; keine Zusatz-Funktionen. |
| Single-Ticket Boundary | OK     | Eine PR, ein Ticket. |

### Details (nur bei VIOLATION)

- Entfällt.

### Suggested Split (nur wenn nötig)

- Kein Split nötig.
```

### Beispiel 2: Scope Violation YES (mit Suggested Split)

**Kontext:** Ticket EHH-55 „Call-Outcome ‚Rückruf vereinbaren‘ speichern“. In der PR: Outcome-Logik + zusätzlich neue Export-Button-Logik + Änderungen an `reporting/utils.ts` (unabhängiger Refactor).

```markdown
## Scope Guard – EHH-55 (Call-Outcome Rückruf speichern)

### Scope Violation: YES

### Prüfergebnis

| Prüfung                | Status    | Kurzbegründung |
|------------------------|-----------|----------------|
| Unrelated Files        | VIOLATION | `reporting/utils.ts` gehört nicht zu Call-Outcome; Refactor ist eigenes Thema. |
| Additional Features    | VIOLATION | Export-Button-Logik ist im Ticket nicht beschrieben. |
| Single-Ticket Boundary | VIOLATION | Drei Themen: Outcome, Export, Reporting-Refactor. |

### Details (nur bei VIOLATION)

- **Fremde/unklare Dateien**: `reporting/utils.ts` (Refactor ohne Ticket-Bezug).
- **Zusatz-Features**: Export-Button / Export-Logik.
- **Grenzüberschreitung**: PR deckt Outcome + Export + Reporting-Refactor ab.

### Suggested Split (nur wenn nötig)

- **Option A (diese PR reduzieren):** Nur Änderungen behalten, die zu EHH-55 gehören: Call-Outcome „Rückruf vereinbaren“ speichern (zugehörige Handler, Events, Tests). Export und `reporting/utils.ts` entfernen.
- **Option B (auslagern):** Export-Button als neues Ticket/PR; Reporting-Refactor (`reporting/utils.ts`) als separates Refactor-Ticket/PR. So bleibt EHH-55 auf einen klaren Scope beschränkt.
```

## Hinweise

- Bei unklarem Ticket-Text: Annahmen kurz notieren und trotzdem ein klares YES/NO abgeben.
- Refactor „im gleichen Modul wie das Feature“ kann OK sein, wenn er dem Ticket zuzuordnen ist; Refactor in fernen Modulen ohne Ticket-Bezug → Unrelated Files.
- Typo-/Format-Fixes in geänderten Dateien sind meist OK; reine Formatierungs-PRs über viele Dateien ohne Ticket-Bezug → prüfen (oft VIOLATION).

## So rufst du den Scope Guard auf

**Minimaler Aufruf (Nutzer liefert Ticket + Änderungen):**

Nutzer sagt z. B.: *„Scope Guard: Ticket EHH-42 – Neues Feld ‚Kündigungsgrund‘ im Lead-Formular. Hier die geänderten Dateien: …“*

Du führst die drei Prüfungen aus und gibst die Ausgabe im festen Format (Scope Violation YES/NO, Tabelle, ggf. Suggested Split) zurück.

**Beispiel-Konversation:**

1. **Nutzer:** „Kannst du prüfen ob diese PR noch zum Ticket EHH-42 passt?“  
2. **Du:** Falls Ticket-Text oder geänderte Dateien fehlen: „Bitte Ticket-Beschreibung bzw. Akzeptanzkriterien und die Liste der geänderten Dateien (oder PR-Link) nennen.“  
3. **Nutzer:** Liefert Ticket + Dateienliste (oder „siehe Branch xyz“).  
4. **Du:** Scope Guard ausführen und Ergebnis im Ausgabe-Format liefern.

**Tipp:** Bei „siehe Branch“ oder „siehe PR“: `git diff` oder Änderungsliste aus dem Repo ermitteln, dann Prüfungen durchführen.
