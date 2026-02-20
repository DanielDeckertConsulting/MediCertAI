---
name: arch-guard
description: Protects system simplicity and prevents overengineering. Checks for unnecessary abstraction, monolith-first consistency, and premature scaling complexity. Use when reviewing architecture decisions, new services, refactorings, or when the user asks about simplicity, abstraction, or scaling.
---

# ARCH_GUARD

Sichert Einfachheit und verhindert Overengineering. Prüft auf unnötige Abstraktion, Monolith-First und verfrühte Skalierung.

## Wann anwenden

Skill anwenden, wenn:

- **Architektur-Entscheidungen** diskutiert oder umgesetzt werden (neue Services, Module, Schichten)
- **Refactorings** oder größere Strukturänderungen anstehen
- Der Nutzer nach **Einfachheit**, **Abstraktion** oder **Skalierung** fragt
- Neue **Abstraktionen**, **Interfaces**, **Adapters** oder **indirekte Schichten** eingeführt werden

## Prüfpunkte

1. **Unnötige Abstraktion**
   - Wird eine Abstraktion/Ebene eingeführt, die aktuell nur eine konkrete Implementierung hat?
   - Würde „direkt aufrufen“ oder „eine Klasse/Modul“ den Bedarf heute decken?
   - Gibt es einen nachweisbaren zukünftigen Wechsel (z. B. zweiter Provider), oder nur Spekulation?

2. **Monolith-First**
   - Ist die Änderung konsistent mit einem monolithischen, einfachen System?
   - Wird unnötig in Richtung Microservices, verteilte Systeme oder „Service-Grenzen“ gedacht?
   - Könnte die Anforderung im bestehenden Monolithen erfüllt werden?

3. **Verfrühte Skalierungs-Komplexität**
   - Werden Caching-, Queue-, Event- oder Replikations-Lösungen eingeführt, ohne dass Last oder Anforderung es erfordern?
   - Wird „später skalierbar“ als Begründung genutzt, ohne messbaren Bedarf?

## Ablauf

1. **Kontext erfassen**: Was wird geändert oder vorgeschlagen (Diff, Ticket, Beschreibung)?
2. **Drei Prüfpunkte** nacheinander anwenden (Abstraktion, Monolith-First, Skalierung).
3. **Overengineering-Flag** setzen und **Vereinfachungsvorschlag** formulieren.
4. **Output-Format** ausgeben.

## Output-Format

Am Ende immer in diesem Format antworten:

```markdown
## ARCH_GUARD – Ergebnis

**Overengineering:** JA | NEIN

**Begründung:** [1–3 Sätze zu den Prüfpunkten, die auffällig waren]

**Vereinfachungsvorschlag:**
- [Konkreter Vorschlag 1, z. B. "Abstraktion entfernen, direkte Nutzung von X"]
- [Vorschlag 2 oder "Keine Änderung nötig"]
- …

**Empfehlung:** [Eine klare Handlungsempfehlung: vereinfachen, so lassen, oder nur dokumentieren]
```

## Checkliste vor Abschluss

- [ ] Alle drei Prüfpunkte (Abstraktion, Monolith-First, Skalierung) berücksichtigt
- [ ] Overengineering-Flag (JA/NEIN) mit kurzer Begründung gesetzt
- [ ] Vereinfachungsvorschläge konkret und umsetzbar formuliert
- [ ] Empfehlung eindeutig (vereinfachen / so lassen / dokumentieren)

## Kurzreferenz

- **Abstraktion:** Erst einführen, wenn mindestens zwei konkrete Fälle existieren oder fest geplant sind.
- **Monolith-First:** Neue Funktionalität zuerst im Monolithen; Service-Aufteilung nur bei nachweisbarem Bedarf.
- **Skalierung:** Caching/Queues/Events erst bei messbarem Leistungs- oder Skalierungsbedarf.
