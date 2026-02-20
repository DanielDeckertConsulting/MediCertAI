# ship-feature-auto: Assistenzmodus Systemprompt-Vorlagen

**MODE_SELECTED:** STANDARD
**DATA_SENSITIVITY:** NONE
**Justification:** Systemprompt-Templates sind Konfigurationsdaten, keine PII. Bearbeitung durch authentifizierte Nutzer. Kein Gesundheitsdatenbezug in den Vorlagen selbst.

## Umgesetzt
- Backend: PATCH /prompts/{key} — neue Version anlegen
- Frontend: getPromptLatest, updatePrompt API
- AssistModesPage: Liste aller 5 Vorlagen, editierbare Textareas, Speichern/Zurücksetzen
- Loading, Empty, Error States
- Tests: test_update_prompt_creates_new_version, test_update_prompt_rejects_empty_body
