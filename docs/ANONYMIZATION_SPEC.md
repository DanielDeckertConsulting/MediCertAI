# ClinAI MVP — Anonymization Specification (V1)

**Status:** Resolved  
**Date:** 2025-02-19

---

## PII Types In Scope for MVP

### 1. Personal Names (Highest Priority)

- First names, last names, full names
- Titles + names (Dr. Müller)
- Patient references: "Herr Schmidt", "Frau Becker"

**Replace with:** `[PATIENT]`, `[THERAPIST]`, `[PERSON_1]`, `[PERSON_2]`

### 2. Contact Information

| Type | Detection | Replacement |
|------|-----------|-------------|
| Email | Regex | `[EMAIL]` |
| Phone | Regex | `[PHONE]` |
| Postal address | Pattern (street + number + zip) | `[ADDRESS]` |

### 3. Identification Numbers

- Insurance numbers, social security, tax IDs, national ID, IBAN, passport numbers

**Replace with:** `[ID_NUMBER]`

### 4. Exact Dates of Birth

- Formats: dd.mm.yyyy, dd/mm/yyyy, yyyy-mm-dd  
**Replace with:** `[DATE_OF_BIRTH]`  
**Do NOT** replace all dates (session dates stay).

### 5. Locations (Limited Scope)

- **In scope:** Full street addresses; exact small town names + person references
- **Out of scope:** Large city names (Berlin, Munich), countries

---

## Explicitly NOT in MVP

- Relationship inference ("my brother Thomas")
- Employer/company anonymization
- Rare disease anonymization
- Contextual quasi-identifier suppression
- Semantic de-identification
- Cross-session pseudonym consistency

---

## MVP Anonymization Levels

| Level | Description |
|-------|-------------|
| Level 0 — Off | Raw text goes to LLM |
| Level 1 — Basic (MVP Default) | Regex + optional NER; replace PII; UI badge "Anonymization Active" |

---

## Implementation

1. **Deterministic regex layer:** Emails, phones, dates of birth, ID formats
2. **Optional NER:** Azure AI Language (PII) or spaCy — PERSON, LOCATION, EMAIL, PHONE, ID
3. Keep everything inside Azure

---

## UI Transparency

When anonymization ON:
- Banner: *"Patient-identifying information has been replaced before processing."*
- Tooltip: *"Basic pattern recognition. Not a guarantee of full anonymization."*

**Never imply perfect de-identification.**

---

## Additional Safeguard

When anonymization is **OFF**:
- Run PII scan before sending to LLM
- If high-confidence name detected → show warning:  
  *"You appear to be entering identifiable patient information. Consider activating anonymization mode."*

---

## V1 Scope Summary

| PII Type | In MVP | Method |
|----------|--------|--------|
| Names | Yes | Regex + NER |
| Email | Yes | Regex |
| Phone | Yes | Regex |
| ID numbers | Yes | Regex |
| Date of Birth | Yes | Regex |
| Full Address | Yes | Regex |
| City Names | No | Too aggressive |
| Employer | No | Out of scope |
| Rare Diseases | No | Contextual |
