---
name: golden-path-protector
description: Protects the Lead → Call → Outcome → Callback → Report flow. Validates end-to-end testability, assesses regression risk, and suggests missing E2E coverage. Use when tickets or changes touch queues, call logic, outcome codes, or reports.
---

# Golden Path Protector

Sichert den Kernfluss **Lead → Call → Outcome → Callback → Report** und bewertet Regressionsrisiko sowie E2E-Abdeckung.

## Wann anwenden

Skill anwenden, wenn Änderungen oder Tickets folgende Bereiche betreffen:

- **Queues** (Lead- oder Call-Queues, Zuweisung, Priorisierung)
- **Call-Logik** (Anruferstellung, Status, Disposition)
- **Outcome-Codes** (Ergebnis-Codes, Klassifikation, Abbruchgründe)
- **Reports** (Auswertungen, Exporte, Dashboards aus dem Flow)

## Ablauf

1. **Betroffene Bereiche identifizieren**  
   Aus Diff/Ticket: Welche der vier Bereiche (Queues, Call, Outcome, Report) werden geändert?

2. **Golden Path testbar prüfen**  
   - Gibt es einen durchgängigen E2E-Test (oder Testkette), der Lead → Call → Outcome → Callback → Report abdeckt?  
   - Sind neue/geänderte Pfade in diesem Flow durch Tests abgedeckt?

3. **Regressionsrisiko bewerten**  
   Siehe Matrix unten → **Regression Risk Level** (LOW / MEDIUM / HIGH) festlegen.

4. **Fehlende Szenarien benennen**  
   Konkrete fehlende E2E-Szenarien als Liste ausgeben.

## Regression Risk Level

| Level | Bedingung |
|-------|-----------|
| **LOW** | Nur Report/Export geändert; Golden Path unverändert; bestehende E2E-Tests decken den Flow ab. |
| **MEDIUM** | Queues, Call-Logik oder Outcome-Codes geändert; E2E-Tests vorhanden, aber geänderte Zweige/Edge-Cases evtl. nicht abgedeckt. |
| **HIGH** | Kern des Flows (Call, Outcome, Callback) geändert ohne passende E2E-Anpassung; oder keine E2E-Tests für den Golden Path. |

## Output-Format

Am Ende immer in diesem Format antworten:

```markdown
## Golden Path Protector – Ergebnis

**Regression Risk Level:** LOW | MEDIUM | HIGH

**Begründung:** [1–2 Sätze]

**Fehlende E2E-Szenarien:**
- [Szenario 1: z. B. "Lead in Queue → Call angelegt → Outcome X → Callback gesetzt → in Report sichtbar"]
- [Szenario 2 oder "Keine identifiziert"]
- …

**Empfehlung:** [Eine konkrete Handlungsempfehlung, z. B. "E2E-Test für neuen Outcome-Code ergänzen" oder "Keine weiteren Schritte nötig."]
```

## Checkliste vor Abschluss

- [ ] Alle vom Ticket/Change betroffenen Bereiche (Queues / Call / Outcome / Report) berücksichtigt
- [ ] Risk Level mit Begründung gesetzt
- [ ] Fehlende Szenarien konkret (Given/When/Then-ähnlich) formuliert
- [ ] Empfehlung ist umsetzbar (Test ergänzen, bestehenden Test anpassen, oder „nichts nötig“)

## Kurzreferenz Golden Path

- **Lead** → Eintritt in den Prozess
- **Call** → Anruf zugeordnet, Status/Disposition
- **Outcome** → Ergebnis-Code gesetzt
- **Callback** → Rückruf geplant/erledigt
- **Report** → Daten im Bericht/Export sichtbar

Änderungen in diesem Flow müssen end-to-end testbar bleiben; fehlende oder veraltete E2E-Tests gelten als Regressionsrisiko.
