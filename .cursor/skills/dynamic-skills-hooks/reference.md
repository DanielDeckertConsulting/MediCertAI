# Hook I/O Reference

## Stop hook stdin (JSON)

The script receives one JSON object on stdin. Example shape:

| Field             | Type   | Description                    |
|-------------------|--------|--------------------------------|
| `conversation_id` | string | Conversation identifier        |
| `status`          | string | `"completed"` \| `"aborted"` \| `"error"` |
| `loop_count`      | number | Current iteration index        |

Other fields may be present; ignore unknown keys.

## Stop hook stdout (JSON)

Output a single JSON object to stdout.

- **Continue the loop**: `{ "followup_message": "string" }` — the agent receives this as the next user message and keeps working.
- **Stop the loop**: `{}` or omit `followup_message`.

No other output (e.g. logs) should go to stdout; use stderr for logging.
