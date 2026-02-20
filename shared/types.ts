/** Shared types for AI Response Rendering Engine. Aligned with shared/events/schema.json */

export type StructuredBlockType =
  | "heading"
  | "paragraph"
  | "list"
  | "table"
  | "code"
  | "divider"
  | "quote"
  | "action";

export interface StructuredBlockBase {
  type: StructuredBlockType;
  content?: string;
  level?: number;
  items?: string[];
  metadata?: Record<string, unknown>;
}

export interface ActionBlock extends StructuredBlockBase {
  type: "action";
  label: string;
  command: string;
  confidence: number;
}

export type StructuredBlock = StructuredBlockBase | ActionBlock;

export interface AIResponse {
  id: string;
  entity_type: string;
  entity_id: string;
  raw_markdown: string;
  structured_blocks: StructuredBlock[];
  model: string;
  confidence: number;
  created_at: string;
  version: number;
}

export interface DomainEventEnvelope {
  event_id: string;
  timestamp: string;
  actor: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  source: string;
  schema_version: string;
  confidence?: number;
  model?: string;
}
