---
name: ac-generator
description: Converts tickets into strict, testable Given/When/Then acceptance criteria. Use when a new ticket is started, when the user asks for acceptance criteria, or when converting a ticket or user story into testable scenarios.
---

# AC-Generator (Acceptance Criteria)

Aus einem Ticket oder einer User Story werden strenge, testbare Akzeptanzkriterien im Given/When/Then-Format erzeugt – inklusive expliziter Annahmen und Abgrenzung zum Out-of-Scope.

## Wann anwenden

- Ein neues Ticket wird gestartet
- Der Nutzer bittet um Akzeptanzkriterien oder Acceptance Criteria
- Ein Ticket/User Story soll in testbare Szenarien überführt werden

## Ausgabe-Struktur (immer verwenden)

Am Ende immer in diesem Format antworten:

```markdown
## Akzeptanzkriterien: [Kurzer Ticket-Titel]

### Given/When/Then (5–15 Szenarien)

1. **Given** [Ausgangslage] **When** [Aktion] **Then** [Erwartetes Ergebnis]
2. **Given** … **When** … **Then** …
…

### Annahmen (explizit)

- [Annahme 1]
- [Annahme 2]
…

### Out-of-Scope

- [Was bewusst nicht abgedeckt ist]
```

## Regeln für Given/When/Then

- **Given**: Eindeutiger, testbarer Ausgangszustand (Daten, Rollen, Systemzustand). Keine vagen Formulierungen.
- **When**: Eine konkrete Aktion (ein Nutzer-Schritt oder ein System-Trigger), keine Mehrfachaktionen in einem Then.
- **Then**: Beobachtbares, prüfbares Ergebnis (UI, API-Response, State, Nachricht). Kein Implementierungsdetail.

Jedes Kriterium muss **einzeln testbar** sein (z. B. Unit-, Integrations- oder E2E-Test).

## Anzahl und Priorisierung

- **5–15** Given/When/Then-Szenarien pro Ticket.
- Zuerst Happy Path, dann wichtige Edge Cases und Fehlerfälle.
- Sehr große Tickets in mehrere AC-Blöcke oder Sub-Tickets aufteilen.

## Annahmen

- Alle impliziten Voraussetzungen explizit machen (z. B. „Nutzer ist eingeloggt“, „Rolle X“, „Daten sind bereits angelegt“).
- Technische oder fachliche Annahmen, die Tests oder Implementierung beeinflussen, auflisten.

## Out-of-Scope

- Klar benennen, was **nicht** in diesem Ticket liegt (andere Features, spätere Phasen, bekannte Limitierungen).
- Verhindert Scope-Creep und falsche Erwartungen.

## Beispiel (gekürzt)

**Ticket:** „Als Recruiter möchte ich einen Lead als ‚erfolgreich kontaktiert‘ markieren können.“

```markdown
### Given/When/Then

1. **Given** ein Lead existiert und ist im Status „Offen“ **When** der Recruiter „Erfolgreich kontaktiert“ wählt **Then** der Lead wechselt in Status „Kontaktiert“ und das Datum wird gespeichert.
2. **Given** ein Lead ist bereits „Kontaktiert“ **When** der Recruiter erneut „Erfolgreich kontaktiert“ wählt **Then** bleibt der Status unverändert und eine Erfolgsmeldung wird angezeigt.
3. **Given** ein Lead existiert **When** der Recruiter die Aktion ohne Berechtigung ausführt **Then** wird die Aktion abgelehnt und ein Fehler angezeigt.
…

### Annahmen

- Nur Nutzer mit Rolle „Recruiter“ oder „Admin“ dürfen den Status setzen.
- „Erfolgreich kontaktiert“ ist ein fester Status-Code im System.

### Out-of-Scope

- Automatische Erinnerungen oder Follow-up-Termine (eigenes Ticket).
- Bulk-Status-Änderung mehrerer Leads (eigenes Ticket).
```

## Checkliste vor Abgabe

- [ ] 5–15 Given/When/Then formuliert
- [ ] Jedes Kriterium einzeln testbar
- [ ] Annahmen-Abschnitt ausgefüllt
- [ ] Out-of-Scope-Abschnitt ausgefüllt
- [ ] Keine vagen Begriffe in Given/When/Then („irgendwann“, „normalerweise“ etc.)
