# Voice-to-Text Dictation Mode — Acceptance Criteria

**Ticket:** As a therapist I want to dictate messages instead of typing **so that** I can document faster during or after sessions.

**Domain events:** None (frontend-only; no backend changes).

**Golden Path impact:** LOW (additive UX).

---

## Akzeptanzkriterien

### Given/When/Then

1. **Given** the chat input is visible and not finalized **When** the user clicks the microphone icon **Then** recording starts and "Aufnahme läuft..." is shown.
2. **Given** recording is active **When** the user clicks the stop button **Then** recording stops and the transcribed text is inserted into the message input.
3. **Given** transcribed text was inserted **When** the user reviews it **Then** they can edit the text before sending.
4. **Given** the user has not granted microphone permission **When** they click the microphone icon **Then** the browser prompts for permission; on deny, a clear error is shown.
5. **Given** Web Speech API is not supported in the browser **When** the user views the chat **Then** the microphone button is hidden or disabled with accessible feedback.
6. **Given** recording is in progress **When** an error occurs (e.g. no speech, network) **Then** a user-friendly error message is shown and recording stops.
7. **Given** the chat input area **When** viewed on 390px viewport **Then** the microphone icon meets 44×44px touch target; no horizontal scroll.
8. **Given** the chat input area **When** viewed on tablet/desktop **Then** the microphone icon is visible and accessible.
9. **Given** dictation **When** text is sent **Then** only text goes to backend; no audio is stored or uploaded.

### Annahmen

- Browser Web Speech API (SpeechRecognition) is used; no Azure Speech-to-Text in MVP.
- German as primary recognition language (browser default or explicit).
- No audio stored, no audio uploaded; compliance preserved.

### Out-of-Scope

- Azure Speech-to-Text integration (Phase 2).
- Waveform visualization (text "Aufnahme läuft..." sufficient for MVP).
- Continuous/background dictation; single start-stop per session.
