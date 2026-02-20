# Test Coverage Auditor – Beispiele

## Beispiel: Vollständiger Audit-Report

**Kontext:** Ticket „Lead als ‚erfolgreich kontaktiert‘ markieren“ mit AC aus dem ac-generator.

### Akzeptanzkriterien (Eingabe)

1. **Given** ein Lead existiert und ist im Status „Offen“ **When** der Recruiter „Erfolgreich kontaktiert“ wählt **Then** der Lead wechselt in Status „Kontaktiert“ und das Datum wird gespeichert.
2. **Given** ein Lead ist bereits „Kontaktiert“ **When** der Recruiter erneut „Erfolgreich kontaktiert“ wählt **Then** bleibt der Status unverändert und eine Erfolgsmeldung wird angezeigt.
3. **Given** ein Lead existiert **When** der Recruiter die Aktion ohne Berechtigung ausführt **Then** wird die Aktion abgelehnt und ein Fehler angezeigt.

### Ausgabe (Coverage-Audit)

```markdown
## Test-Coverage-Audit: Lead „Erfolgreich kontaktiert“ markieren

### Coverage Map (AC → Test)

| # | Akzeptanzkriterium (Given/When/Then) | Gedeckt | Test(s) |
|---|-------------------------------------|---------|---------|
| 1 | Given Lead existiert, Status „Offen“ When Recruiter wählt „Erfolgreich kontaktiert“ Then Status „Kontaktiert“, Datum gespeichert | ✅ | `src/leads/lead-status.test.ts::markAsContacted updates status and sets date` |
| 2 | Given Lead „Kontaktiert“ When erneut „Erfolgreich kontaktiert“ Then Status unverändert, Erfolgsmeldung | ❌ | — |
| 3 | Given Lead existiert When Aktion ohne Berechtigung Then abgelehnt, Fehler | ✅ | `src/leads/lead-status.test.ts::markAsContacted rejects when user lacks permission` |

### Fehlende Tests

- **AC #2**: Lead bereits kontaktiert → erneute Auswahl → Idempotenz (Status bleibt, Erfolgsmeldung). *Empfohlener Test:* In `lead-status.test.ts` einen Test `markAsContacted when already contacted leaves status unchanged and returns success message` ergänzen (Given: Lead mit Status „Kontaktiert“, When: markAsContacted, Then: Status unverändert, Response OK).

### Zusammenfassung

- Gedeckt: 2 / 3 AC
- Fehlend: 1 AC
```

---

## Typische Test-Suchpfade (Projekt anpassen)

Beim Schritt „Tests finden“ im Ablauf nach folgenden Mustern suchen; sobald im Projekt Tests existieren, die konkreten Pfade ergänzen.

| Stack | Typische Dateien / Verzeichnisse |
|-------|----------------------------------|
| **TypeScript/JavaScript (Jest, Vitest)** | `**/*.test.{ts,tsx,js,jsx}`, `**/*.spec.{ts,tsx,js,jsx}`, `**/__tests__/**`, `**/tests/**` |
| **Python (pytest)** | `**/test_*.py`, `**/*_test.py`, `**/tests/**` |
| **Backend/API** | Oft `**/api/**/*.test.*`, `**/handlers/**/*.spec.*` oder analog zu Modulstruktur |

**Referenz im Test:** In der Coverage Map immer **Dateipfad + Testname** angeben, z. B.:

- Jest/Vitest: `path/to/file.test.ts::describe name :: it name` oder `file.test.ts` + `it('...')`-Text
- pytest: `path/to/test_module.py::test_function_name`

So können fehlende Tests und Empfehlungen konkret einer Datei/ einem Block zugeordnet werden.
