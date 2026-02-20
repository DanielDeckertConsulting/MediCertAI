/** Renders chat message content as Markdown. **Headline** on its own line = heading-style. */
import React from "react";

/** Parse and render markdown-like content. Supports **bold**, ## headings, - lists, and **Headline** as headings. */
export function ChatMessageMarkdown({ content }: { content: string }) {
  if (!content?.trim()) return null;

  const lines = content.split(/\r?\n/);
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={elements.length} className="my-2 list-disc pl-5 space-y-0.5">
          {listItems.map((item, i) => (
            <li key={i} className="text-sm">
              {renderInlineMarkdown(item)}
            </li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  const renderInlineMarkdown = (text: string) => {
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    const boldRe = /\*\*([^*]+)\*\*/g;
    let m: RegExpExecArray | null;
    while ((m = boldRe.exec(text)) !== null) {
      if (m.index > lastIndex) {
        parts.push(text.slice(lastIndex, m.index));
      }
      parts.push(<strong key={m.index} className="font-semibold">{m[1]}</strong>);
      lastIndex = m.index + m[0].length;
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts.length > 1 ? <>{parts}</> : text || null;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? "";
    const trimmed = line.trim();

    if (trimmed.startsWith("- ")) {
      listItems.push(trimmed.slice(2));
      continue;
    }
    flushList();

    if (!trimmed) {
      elements.push(<br key={elements.length} />);
      continue;
    }

    // ## Heading
    const h2Match = trimmed.match(/^##\s+(.+)$/);
    if (h2Match?.[1]) {
      elements.push(
        <h3 key={elements.length} className="mt-3 mb-1 text-base font-semibold first:mt-0">
          {renderInlineMarkdown(h2Match[1].trim())}
        </h3>
      );
      continue;
    }

    // **Headline** on own line or "N. **Headline**:" — treat as heading
    const headlineMatch = trimmed.match(/^(\d+\.\s*)?\*\*([^*]+)\*\*:?\s*$/);
    if (headlineMatch?.[2]) {
      elements.push(
        <h3 key={elements.length} className="mt-3 mb-1 text-base font-semibold first:mt-0">
          {headlineMatch[1] && <span className="mr-1">{headlineMatch[1]}</span>}
          {headlineMatch[2].trim()}
        </h3>
      );
      continue;
    }

    elements.push(
      <p key={elements.length} className="my-1 text-sm leading-relaxed first:mt-0 last:mb-0">
        {renderInlineMarkdown(trimmed)}
      </p>
    );
  }
  flushList();

  return <div className="space-y-1 [&>*:first-child]:mt-0">{elements}</div>;
}
