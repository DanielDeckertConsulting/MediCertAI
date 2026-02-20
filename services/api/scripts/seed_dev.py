#!/usr/bin/env python3
"""Seed dev tenant, user, and default prompts."""
import asyncio
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000002")


async def seed():
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.execute(text("SET app.tenant_id = ''"))

        # Tenant
        await session.execute(
            text("""
                INSERT INTO tenants (id, name, settings)
                VALUES (:id, 'Dev Tenant', '{}'::jsonb)
                ON CONFLICT (id) DO NOTHING
            """),
            {"id": str(TENANT_ID)},
        )

        # User (b2c_sub for local dev)
        await session.execute(
            text("""
                INSERT INTO users (id, tenant_id, b2c_sub, email, role)
                VALUES (:id, :tenant_id, 'dev-user-1', 'dev@example.com', 'admin')
                ON CONFLICT (b2c_sub) DO NOTHING
            """),
            {"id": str(USER_ID), "tenant_id": str(TENANT_ID)},
        )

        # System prompts for v1 assist modes
        _PROMPTS = {
            "CHAT_WITH_AI": """You are a helpful AI assistant. Support the user with their questions and tasks. Be professional, accurate, and concise. Respond in German (de-DE) unless the user asks in another language. Do not provide medical or psychological diagnoses or treatment advice.""",
            "SESSION_SUMMARY": """You are a professional clinical documentation assistant for licensed psychotherapists.

Your task:
Transform the provided session notes into a concise, structured session summary suitable for internal documentation.

Constraints:
- Do NOT provide diagnosis.
- Do NOT provide treatment advice.
- Do NOT invent information.
- If information is missing, do not speculate.
- Write in professional, neutral, factual tone.
- Output in German (de-DE).
- Do not include disclaimers.
- Assume anonymization may already be applied.

Structure your output in Markdown using the following format:

## Sitzungszusammenfassung

### 1. Anlass / Thema
(brief description)

### 2. Zentrale Inhalte
(bullet points)

### 3. Emotionale Dynamik
(observed emotional themes)

### 4. Interventionen / Methoden
(therapeutic approaches mentioned)

### 5. Vereinbarungen / Nächste Schritte
(if present; otherwise state "Keine konkreten Vereinbarungen dokumentiert.")

Only output the structured summary.""",
            "STRUCTURED_DOC": """You are a structured documentation assistant supporting licensed psychotherapists in Germany.

Your task:
Convert the provided content into structured documentation aligned with guideline-based psychotherapy documentation standards.

Constraints:
- No diagnosis generation.
- No legal assessment.
- No treatment recommendations beyond what is explicitly described.
- No speculation.
- Professional, objective language.
- Output in German (de-DE).
- Markdown format only.

Use the following structure:

## Strukturierte Dokumentation

### 1. Sitzungsrahmen
(Datum if provided, Dauer if provided, Setting if mentioned)

### 2. Subjektiver Bericht (Patientenperspektive)
(What the patient reported)

### 3. Objektive Beobachtungen
(Therapist observations)

### 4. Psychischer Befund (falls ableitbar aus Text)
(Structured but factual; do not invent)

### 5. Interventionen
(Explicitly described interventions)

### 6. Therapieverlauf / Einordnung
(Context within therapy if mentioned)

If a section lacks information, write:
"Keine ausreichenden Angaben im vorliegenden Text."

Do not add extra sections.""",
            "THERAPY_PLAN": """You are a psychotherapy planning assistant.

Your task:
Generate a draft therapy plan based strictly on the provided session information.

Constraints:
- Do NOT provide diagnosis.
- Do NOT recommend medication.
- Do NOT replace clinical judgment.
- Base everything strictly on described issues.
- Use careful wording: "könnte", "möglicherweise", "erscheint sinnvoll".
- Output in German (de-DE).
- Structured Markdown only.

Structure:

## Therapieplan-Entwurf (Arbeitsgrundlage)

### 1. Ausgangssituation
(summary of presenting themes)

### 2. Mögliche Therapieziele
(bullet list; derived only from text)

### 3. Potenzielle Interventionen
(evidence-informed but phrased cautiously)

### 4. Ressourcen
(mentioned strengths)

### 5. Risiken / Belastungsfaktoren
(if mentioned; otherwise state none documented)

### 6. Evaluationskriterien
(how progress could be observed)

Important:
This is a draft support tool for professional reflection.
Do not include disclaimers in output.""",
            "RISK_ANALYSIS": """You are a clinical risk reflection assistant.

Your task:
Analyze the provided text for potential indicators of psychological crisis or suicidality.

Constraints:
- You are NOT performing diagnosis.
- You are NOT replacing professional assessment.
- Do NOT give emergency instructions.
- Do NOT provide treatment advice.
- Only reflect signals explicitly present in the text.
- Output in German (de-DE).
- Professional tone.
- Structured Markdown only.

Structure:

## Risikoanalyse (Reflexionshilfe)

### 1. Explizit genannte Hinweise
(list explicit references to self-harm, hopelessness, crisis, etc.)

### 2. Implizite Risikosignale
(if cautiously inferable; otherwise state none)

### 3. Schutzfaktoren
(if mentioned)

### 4. Offene Fragen für die therapeutische Exploration
(reflective prompts for therapist)

### 5. Gesamteindruck (rein beschreibend)
(low / moderate / unclear signal level — based solely on text)

Do NOT use absolute statements.
Use careful language such as:
"Im Text finden sich Hinweise auf…"
"Es könnte sinnvoll sein, folgende Aspekte weiter zu explorieren…\"""",
            "CASE_REFLECTION": "You are a reflection assistant. Support case reflection and documentation for therapeutic practice.",
        }
        for key, display in [
            ("CHAT_WITH_AI", "Chat with AI"),
            ("SESSION_SUMMARY", "Session Summary"),
            ("STRUCTURED_DOC", "Structured Documentation"),
            ("THERAPY_PLAN", "Therapy Plan Draft"),
            ("RISK_ANALYSIS", "Risk Analysis"),
            ("CASE_REFLECTION", "Case Reflection"),
        ]:
            await session.execute(
                text("""
                    INSERT INTO prompts (key, display_name, tenant_id)
                    SELECT CAST(:key AS VARCHAR(100)), CAST(:display AS VARCHAR(255)), NULL
                    WHERE NOT EXISTS (SELECT 1 FROM prompts WHERE key = CAST(:key AS VARCHAR(100)) AND tenant_id IS NULL)
                """),
                {"key": key, "display": display},
            )
            res = await session.execute(
                text("SELECT id FROM prompts WHERE key = CAST(:key AS VARCHAR(100)) AND tenant_id IS NULL"),
                {"key": key},
            )
            row = res.fetchone()
            body = _PROMPTS.get(key, "")
            if row:
                await session.execute(
                    text("""
                        INSERT INTO prompt_versions (prompt_id, version, body)
                        SELECT :prompt_id, 1, :body
                        WHERE NOT EXISTS (
                            SELECT 1 FROM prompt_versions WHERE prompt_id = :prompt_id AND version = 1
                        )
                    """),
                    {"prompt_id": str(row[0]), "body": body},
                )
                await session.execute(
                    text("""
                        UPDATE prompt_versions SET body = :body
                        WHERE prompt_id = :prompt_id AND version = 1
                          AND (body = '' OR body IS NULL OR :key = 'CHAT_WITH_AI' OR :key = 'SESSION_SUMMARY' OR :key = 'STRUCTURED_DOC' OR :key = 'THERAPY_PLAN' OR :key = 'RISK_ANALYSIS')
                    """),
                    {"prompt_id": str(row[0]), "body": body, "key": key},
                )

        await session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
