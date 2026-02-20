/** AI Response Renderer — structured blocks only. Mobile-first. */
import { useState, useCallback } from "react";
import type { StructuredBlock } from "../api/client";

function BlockHeading({ block }: { block: StructuredBlock }) {
  const Tag = `h${Math.min((block.level ?? 1) + 1, 6)}` as keyof JSX.IntrinsicElements;
  return (
    <Tag className="mt-4 first:mt-0 font-semibold text-gray-900 dark:text-white">
      {block.content}
    </Tag>
  );
}

function BlockParagraph({ block }: { block: StructuredBlock }) {
  return (
    <p className="mt-2 text-sm leading-relaxed text-gray-700 dark:text-gray-200 whitespace-pre-wrap">
      {block.content}
    </p>
  );
}

function BlockList({ block }: { block: StructuredBlock }) {
  const items = block.items ?? [];
  return (
    <ul className="mt-2 list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-200">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function BlockQuote({ block }: { block: StructuredBlock }) {
  return (
    <blockquote className="mt-2 border-l-4 border-primary-300 pl-3 py-1 text-sm italic text-gray-600 dark:text-gray-300">
      {block.content}
    </blockquote>
  );
}

function BlockCode({
  block,
  onCopy,
}: {
  block: StructuredBlock;
  onCopy?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(() => {
    if (block.content) {
      navigator.clipboard.writeText(block.content);
      setCopied(true);
      onCopy?.();
      setTimeout(() => setCopied(false), 1500);
    }
  }, [block.content, onCopy]);
  return (
    <div className="mt-2 rounded-lg bg-gray-100 dark:bg-gray-800 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {(block.metadata as { language?: string })?.language || "code"}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          className="min-h-touch min-w-touch rounded px-2 py-1 text-xs text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/30 dark:text-primary-400"
        >
          {copied ? "Kopiert" : "Kopieren"}
        </button>
      </div>
      <pre className="p-3 overflow-x-auto text-xs text-gray-800 dark:text-gray-200">
        <code>{block.content}</code>
      </pre>
    </div>
  );
}

function BlockTable({ block }: { block: StructuredBlock }) {
  const rows = (block as { items?: string[][] }).items ?? [];
  return (
    <div className="mt-2 overflow-x-auto -mx-2">
      <table className="min-w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
        <tbody>
          {rows.map((row, r) => (
            <tr
              key={r}
              className={r % 2 === 0 ? "bg-white dark:bg-gray-800" : "bg-gray-50 dark:bg-gray-700/50"}
            >
              {row.map((cell, c) => (
                <td
                  key={c}
                  className="px-3 py-2 border-b border-gray-200 dark:border-gray-600 last:border-b-0"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BlockDivider() {
  return <hr className="my-4 border-gray-200 dark:border-gray-600" />;
}

function BlockAction({
  block,
  onExecute,
  needsReview,
}: {
  block: StructuredBlock;
  onExecute?: () => void;
  needsReview?: boolean;
}) {
  const label = block.label ?? block.command ?? "Ausführen";
  const conf = block.confidence ?? 0;
  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={onExecute}
        className="min-h-touch min-w-[min(100%,320px)] w-full rounded-lg bg-primary-500 px-4 py-3 text-sm font-medium text-white hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 touch-manipulation"
      >
        {label}
      </button>
      <div className="mt-1 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <span title={`Confidence: ${(conf * 100).toFixed(0)}%`}>
          {(conf * 100).toFixed(0)}% Vertrauen
        </span>
        {needsReview && (
          <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
            Review empfohlen
          </span>
        )}
      </div>
    </div>
  );
}

export interface AIResponseRendererProps {
  blocks: StructuredBlock[];
  confidence?: number;
  needsReview?: boolean;
  onActionClick?: (block: StructuredBlock) => void;
}

export default function AIResponseRenderer({
  blocks,
  confidence = 1,
  needsReview = false,
  onActionClick,
}: AIResponseRendererProps) {
  return (
    <div className="space-y-2 text-left">
      {confidence < 1 && (
        <div className="flex items-center gap-2 rounded-lg bg-gray-100 dark:bg-gray-800 px-3 py-2">
          <span className="text-sm text-gray-600 dark:text-gray-300">
            KI-Vertrauen: {(confidence * 100).toFixed(0)}%
          </span>
          {needsReview && (
            <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
              Review empfohlen
            </span>
          )}
        </div>
      )}
      {blocks.map((block, i) => {
        switch (block.type) {
          case "heading":
            return <BlockHeading key={i} block={block} />;
          case "paragraph":
            return <BlockParagraph key={i} block={block} />;
          case "list":
            return <BlockList key={i} block={block} />;
          case "quote":
            return <BlockQuote key={i} block={block} />;
          case "code":
            return <BlockCode key={i} block={block} />;
          case "table":
            return <BlockTable key={i} block={block} />;
          case "divider":
            return <BlockDivider key={i} />;
          case "action":
            return (
              <BlockAction
                key={i}
                block={block}
                onExecute={onActionClick ? () => onActionClick(block) : undefined}
                needsReview={needsReview}
              />
            );
          default:
            return block.content ? (
              <BlockParagraph key={i} block={block} />
            ) : null;
        }
      })}
    </div>
  );
}
