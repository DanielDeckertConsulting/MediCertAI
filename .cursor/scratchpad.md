# Voice-to-Text Dictation Mode — ship-feature-auto

MODE_SELECTED=STANDARD
DATA_SENSITIVITY=NONE

**Justification:**
- No audio stored; no audio uploaded
- Only transcribed text sent to backend (existing chat flow)
- Frontend-only (browser Web Speech API)
- No PII beyond what user already types
- No auth/infra changes

**Gates:** DOCS (user-facing flow); optional RESPONSIVE_AUDIT (mobile)

---

## PR Notes

**What changed:**
- New `VoiceInputButton` component: Web Speech API (SpeechRecognition/webkitSpeechRecognition), German lang; microphone icon near chat input
- Start recording → "Aufnahme läuft..." → stop → insert transcript; user can edit before send
- No audio stored/uploaded; only text sent; button hidden when API unsupported
- ChatPage: VoiceInputButton integrated; text appended to input (or replaces if empty)
- AC: `docs/tickets/voice-dictation-ac.md`; flow: `docs/diagrams/voice-dictation-flow.md`

**How to test:**
1. Chrome/Edge: open /chat, grant mic permission, click mic → speak → click stop → text in input
2. Firefox: mic button not shown (unsupported)
3. 390px viewport: mic 44×44px, no horizontal scroll

**Golden Path impact:** LOW

---

# Cross-Conversation Knowledge Extraction (Case Summary View) — ship-feature-auto

MODE_SELECTED=HEALTHCARE
DATA_SENSITIVITY=HEALTHCARE_SENSITIVE

**Justification:**
- Case summary across conversations: clinical support tooling, patient/therapy context
- Regulatory sensitivity: approaches clinical support; requires draft-only, no diagnosis, disclaimer
- Audit requirement: cross_case_summary_generated
- PII/healthcare data: messages contain therapy content

---

## PR Notes

**What changed:**
- Backend: `POST /cases/summary` with `conversation_ids`; validates same tenant; fetches messages; runs summarization prompt (no diagnosis, no treatment recommendation); returns structured `case_summary`, `trends`, `treatment_evolution`; audit `cross_case_summary_generated`
- Frontend: "Fallzusammenfassung generieren" button in ChatList when folder selected + chats exist; modal with structured output and disclaimer "KI-gestützte Zusammenfassung – keine diagnostische Entscheidung."
- `chat_completion` (non-streaming) added to azure_openai.py for summarization

**How to test:**
1. Create folder, assign chats with messages, select folder in Chat view
2. Click "Fallzusammenfassung generieren" → modal opens, loading then summary
3. Verify disclaimer visible, no diagnosis wording in output
4. `cd services/api && pytest tests/test_cases.py -v`

**Compliance:** No automatic storage; no diagnosis; no treatment recommendation; audit metadata only

**Golden Path impact:** LOW (additive feature)

## Ticket (Stage 1)
**As a** healthcare professional **I want** a visible safety indicator below AI responses **so that** I know the content requires professional review.

**Scope:** Static badge "KI-Entwurf – fachliche Prüfung erforderlich."; optional confidence when available.
**Out of scope:** Backend logprobs extraction (Phase 2); no LLM change.

## AC (Stage 2)
1. **Given** an AI response is displayed **When** the user views it **Then** a small muted badge "KI-Entwurf – fachliche Prüfung erforderlich." appears below.
2. **Given** AI response metadata includes confidence (0–1) **When** displayed **Then** badge shows "KI-Entwurf (Modellvertrauen: X%) – fachliche Prüfung erforderlich."
3. **Given** a user message **When** displayed **Then** no badge appears (user messages only).
4. **Given** the badge **When** viewed on 390px/768px/desktop **Then** responsive layout is preserved.
5. **Given** the badge **When** viewed **Then** styling is small text, subtle gray, non-alarming.

Golden Path impact: LOW. No domain events (UI-only).

---

**Justification:**
- UI-only change: safety badge below AI responses
- No PII, no healthcare data in the indicator
- No auth/infra changes
- Optional backend metadata (confidence) when available; static badge for basic version

---

## PR Notes

**What changed:**
- New `AIConfidenceBadge` component: small muted text "KI-Entwurf – fachliche Prüfung erforderlich."; optional "Modellvertrauen: X%" when confidence provided.
- ChatPage: badge below each assistant message (including streaming).
- AIResponseRenderer: always shows badge below blocks; passes confidence when available.
- Removed old top-level confidence/needsReview block from AIResponseRenderer (BlockAction still shows per-action confidence).

**How to test:**
1. Chat: Open /chat, send message → AI response shows badge below.
2. KI-Antworten: Open /ai-responses, process markdown → badge with confidence if provided.
3. Mobile: 390px viewport — no horizontal scroll, badge readable.

**Assumptions:**
- Chat streaming does not return confidence (static badge only).
- AIResponsesPage continues to pass confidence from processAIMarkdown response.

**Follow-ups:**
- Phase 2: Backend capture of logprobs/confidence from Azure OpenAI when available.

RELEASE_READINESS_TLDR:
- Status: ✅ Ready (or ⚠️ Needs follow-up: <1 line>)
- Impact: <LOW|MEDIUM|HIGH> | Complexity: <LOW|MEDIUM|HIGH>
- Gates: Tests ✅ | Review (<QUICK|DEEP>) ✅ | E2E <NONE|SMOKE|FULL> ✅
- Key risk: <one liner>
