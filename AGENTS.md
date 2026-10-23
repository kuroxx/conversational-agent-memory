# Repository guide for coding agents

## Purpose

This repository demonstrates a bakery assistant that maintains customer context across Twilio SMS
and Voice. Keep changes focused and preserve the distinction between durable customer memory,
short-lived session state, Enterprise Knowledge, and live order data.

## Environment

- Use Python 3.11 or newer.
- Install development dependencies with `pip install -e ".[dev]"`.
- Copy `.env.example` to `.env` for local configuration.
- Never commit `.env`, API keys, authentication tokens, phone numbers, or generated customer data.
- Treat setup, messaging, calling, and cleanup scripts as operations that can affect external
  resources. Do not run them unless the user explicitly requests it.

## Project layout

- `src/conversation_agent/main.py`: FastAPI, channel wiring, and Voice/SMS response routing.
- `src/conversation_agent/agent.py`: instructions, working-memory sessions, and model execution.
- `src/conversation_agent/tools/`: tools grouped by domain.
  - `memory.py`: customer-memory recall.
  - `knowledge.py`: Enterprise Knowledge search.
  - `messaging.py`: outbound SMS.
  - `orders.py`: order mutations.
  - `provider.py`: assembles tools available to a conversation.
- `src/conversation_agent/order_store.py`: simulated live order state.
- `scripts/`: setup, seeding, verification, cleanup, and API helpers.
- `assets/bakery_knowledge.md`: fictional bakery policies indexed by Enterprise Knowledge.
- `RUNBOOK.md`: setup, development, and resource cleanup instructions.

## Design conventions

- Keep `agent.py` concise; put tool implementation details in the appropriate domain module.
- Stream Voice responses through `VoiceChannel.send_response()` and return `None` from the TAC
  callback after sending. Messaging callbacks return a complete string.
- Preserve `SQLiteSession` history per conversation and clear it when the conversation ends.
- Build customer-specific tools from `ConversationSession` rather than storing customer identity in
  global state.
- Expose memory recall only when the session has a resolved profile.
- Keep Voice memory retrieval set to `once` for latency and messaging retrieval set to `always` for
  freshness unless the task explicitly changes that tradeoff.
- Treat Enterprise Knowledge as reference content, not customer memory.
- Read live order status from the order store or relevant service; do not represent it as durable
  memory.
- Preserve the latest verified value when customer information is corrected.
- Do not turn temporary statements into durable profile traits.
- Do not claim that an order changed or a message was sent unless the corresponding tool succeeded.
- Keep user-facing agent responses short and conversational.
- Keep `ModelSettings(store=False)` and hosted tracing disabled for Zero Data Retention projects.

## Python style

- Follow the Ruff configuration in `pyproject.toml` and the 100-character line limit.
- Add type annotations to public functions and methods.
- Prefer small domain-focused modules and explicit dependency injection.
- Use async APIs for network operations.
- Avoid unnecessary abstractions for this intentionally small demo.

## Validation

Run these checks after changing Python code:

```bash
ruff format src scripts
ruff check src scripts
python -m compileall -q src scripts
```

When behavior changes, exercise the relevant channel path. Tests must not send real messages, place
calls, provision resources, or delete Twilio resources unless the user explicitly requests the
external operation.

## Documentation

- Update `README.md` when setup steps or project structure change.
- Update `RUNBOOK.md` when setup or project operations change.
- Keep `.env.example` synchronized with required configuration without including real values.
