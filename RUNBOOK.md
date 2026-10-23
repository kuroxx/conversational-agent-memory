# Project runbook

> Before you begin, complete the [project prerequisites](README.md#prerequisites).

> **Note for Zero Data Retention organizations:** The default Responses API call can fail with
> `Items are not persisted for Zero Data Retention organizations.` Set
> `ModelSettings(store=False)` on the agent to disable response storage. This project also calls
> `set_tracing_disabled(True)` to prevent the Agents SDK from sending hosted traces.

## Quickstart

### 1. Install dependencies

Create a virtual environment and install the project.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure the environment

Copy the example environment file.

```bash
cp .env.example .env
```

Set the OpenAI key, Twilio credentials, Twilio phone number, demo customer phone number,
and public domain in `.env`. Use only the public hostname for
`TWILIO_VOICE_PUBLIC_DOMAIN`, without a protocol or path. Leave the generated resource IDs
empty for now.

### 3. Provision Twilio resources

Create the Conversation Memory store and Conversation Orchestrator configuration.

```bash
python -m scripts.setup
```

Copy the two generated IDs into the matching fields in `.env`.

### 4. Configure the Voice webhook

In the Twilio Console, configure the phone number's incoming Voice webhook to send a `POST`
request to `https://<your-domain>/twiml`.

### 5. Seed the customer profile

Create the known customer profile and its initial order memory, then run the preflight checks.

```bash
python -m scripts.seed_profile
python -m scripts.verify_demo
```

### 6. Seed Enterprise Knowledge

Create the Owl Bakery knowledge base and index the fictional policies.

```bash
python -m scripts.seed_knowledge
```

Copy the printed `TWILIO_KNOWLEDGE_BASE_ID` into `.env`. Edit
`assets/bakery_knowledge.md` before running the command to change the policies. If your Twilio
account doesn't have Enterprise Knowledge access, skip this step and leave the ID empty; the
agent runs without the `search_bakery_knowledge` tool.

### 7. Run the application

```bash
./run.sh
```

Open `http://localhost:8000/health` to confirm that the server is running.

## Development

Run the project checks:

```bash
ruff check src scripts
```

## Resource cleanup

Delete an individual demo resource by its Twilio ID:

```bash
python -m scripts.cleanup <kind> <resource-id>
```

Supported kinds are `memory`, `orchestrator`, `intelligence`, `knowledge`, and `profile`.
The command asks you to type `yes` before deleting it; pass `--yes` only for intentional
non-interactive cleanup. Memory Store and Knowledge Base deletions also remove their child resources.
