/** SSE streaming for chat messages. */
import { apiFetchStream } from "./client";

export interface StreamCallbacks {
  onToken: (text: string) => void;
  onDone: (data: { message_id: string; usage?: { prompt_tokens?: number; completion_tokens?: number } }) => void;
  onError: (message: string) => void;
}

export async function streamChatMessage(
  chatId: string,
  body: { assist_mode_key: string; anonymization_enabled: boolean; safe_mode?: boolean; user_message: string },
  callbacks: StreamCallbacks
): Promise<void> {
  const res = await apiFetchStream(`/chats/${chatId}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;
    try {
      const json = (await res.json()) as { detail?: string; message?: string };
      detail = json.detail ?? json.message ?? detail;
    } catch {
      try {
        detail = (await res.text()) || detail;
      } catch {
        /* ignore */
      }
    }
    callbacks.onError(detail);
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError("No response body");
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      let event = "";
      for (const line of lines) {
        if (line.startsWith("event:")) {
          event = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (!data) continue;
          try {
            const obj = JSON.parse(data) as Record<string, unknown>;
            if (event === "token" && typeof obj.text === "string") {
              callbacks.onToken(obj.text);
            } else if (event === "done") {
              callbacks.onDone({
                message_id: (obj.message_id as string) ?? "",
                usage: obj.usage as { prompt_tokens?: number; completion_tokens?: number },
              });
            } else if (event === "error") {
              callbacks.onError((obj.message as string) ?? "Unknown error");
            }
          } catch {
            // ignore parse errors for unknown events
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
