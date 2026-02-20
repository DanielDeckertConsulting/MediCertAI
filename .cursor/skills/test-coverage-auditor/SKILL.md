---
name: test-coverage-auditor
description: Maps acceptance criteria (Given/When/Then) to test cases and reports missing coverage. Use when verifying that AC are covered by tests, when auditing test coverage for a ticket, when the user asks which tests cover which requirements, or before merging to ensure AC are tested.
---

# Test Coverage Auditor

Prüft, ob Akzeptanzkriterien (AC) durch Tests abgedeckt sind. Liefert eine Coverage-Map (AC → Test) und listet fehlende Tests.

## Wann anwenden

- Vor Merge: Sicherstellen, dass alle AC eines Tickets getestet sind
- Nach Erstellung von AC (z. B. mit ac-generator): Prüfen, ob Tests existieren oder fehlen
- Nutzer fragt: „Welche Tests decken diese Anforderung ab?“ oder „Fehlen Tests für die AC?“
- Audit: Systematische Prüfung der Testabdeckung für ein Feature oder Ticket

## Ablauf

1. **AC sammeln**: Aus Ticket, Kommentar oder bereits generierten Given/When/Then-Szenarien (z. B. ac-generator-Format). Jedes Szenario = eine AC-Zeile.
2. **Tests finden**: Im Projekt nach Testdateien/Testfällen suchen (z. B. `*_test.*`, `*.spec.*`, `describe`/`it`, `@Test`, pytest).
3. **Zuordnung**: Pro AC prüfen, welcher Test (Datei + Testname/ID) das Verhalten abdeckt. Semantische Äquivalenz: Test prüft dasselbe Given/When/Then (oder erkennbare Teilmenge).
4. **Ausgabe erzeugen**: Coverage-Map und Liste fehlender Tests im vorgegebenen Format ausgeben.

## Ausgabe-Format (immer verwenden)

Am Ende der Prüfung immer in diesem Format antworten:

```markdown
## Test-Coverage-Audit: [Kurzer Ticket-/Feature-Titel]

### Coverage Map (AC → Test)

| # | Akzeptanzkriterium (Given/When/Then) | Gedeckt | Test(s) |
|---|-------------------------------------|---------|---------|
| 1 | Given … When … Then …               | ✅ / ❌  | `path/to/test.ext::test_name` oder — |
| 2 | …                                   | …       | … |

### Fehlende Tests

- **AC #X**: [Kurze Beschreibung des Szenarios]. *Empfohlener Test:* [Datei/Describe-Name oder konkrete Testidee]
- …

### Zusammenfassung

- Gedeckt: X / Y AC
- Fehlend: Z AC
```

- **Gedeckt**: ✅ wenn mindestens ein Test das Szenario (oder eine erkennbare Teilmenge) abdeckt; ❌ sonst.
- **Test(s)**: Konkreter Pfad + Testname/ID; bei mehreren Tests kommagetrennt. Bei ❌: "—" oder "–".
- **Fehlende Tests**: Nur Zeilen mit ❌; pro AC eine Zeile mit Empfehlung für einen neuen Test.

## Zuordnungsregeln

- **Eindeutige Zuordnung**: Ein Test kann mehrere AC abdecken (z. B. ein E2E-Test für mehrere Thens). Ein AC kann von mehreren Tests abgedeckt sein (z. B. Unit + Integration). In der Map alle relevanten Tests angeben.
- **Semantik**: Der Test muss dasselbe Verhalten prüfen (gleicher Kontext, Aktion, erwartetes Ergebnis). Nur Dateiname/Testname reicht nicht – kurz begründen, warum der Test die AC deckt, wenn es nicht offensichtlich ist.
- **Unklare Fälle**: Wenn unklar ist, ob ein Test eine AC deckt → als ❌ werten und in „Fehlende Tests“ mit Hinweis „Evtl. abgedeckt durch [Test], bitte manuell prüfen“ aufführen.

## Checkliste vor Abgabe

- [ ] Alle AC aus dem Ticket/der Quelle in der Coverage Map aufgeführt
- [ ] Jede Zeile mit ✅ oder ❌ und konkreten Testreferenzen bzw. "—"
- [ ] Abschnitt „Fehlende Tests“ nur für AC mit ❌, mit kurzer Empfehlung
- [ ] Zusammenfassung (X/Y gedeckt, Z fehlend) stimmig
- [ ] Antwort auf Deutsch (wie Projektvorgabe)

## Weitere Ressourcen

- Für ein ausgefülltes Audit-Beispiel und typische Test-Suchpfade siehe [examples.md](examples.md).
