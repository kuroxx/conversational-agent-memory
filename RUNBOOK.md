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

Set the OpenAI key, Twilio credentials, Twilio phone number, demo customer name and phone number,
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
Rerun the seed command after changing `DEMO_CUSTOMER_FIRST_NAME` to update an existing profile.

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

## Test the demo story

Use the phone configured as `DEMO_CUSTOMER_PHONE` so the agent can resolve the seeded profile.

1. Call the Twilio number and say, "Hi, do you remember me?"
   Confirm that the agent uses the name configured as `DEMO_CUSTOMER_FIRST_NAME`.
2. Say, "What did we previously discuss about my birthday cake?"
   Confirm that the agent recalls the request to change order `4521` from pickup to delivery and
   the need to provide a delivery time.
3. Say, "Please deliver it between 2 and 4 PM to 24 Rose Lane. Go ahead and update the order."
   Confirm that the agent reports the change only after the order update succeeds.
4. Say, "What does the cake inscription say?"
   Confirm that the agent reads the current order data and answers, "Happy Birthday Maya!"
5. Say, "Please text me a confirmation."
   Confirm that the SMS arrives before the agent claims it was sent.
6. Reply by SMS, "Thanks. What's the latest status of my birthday cake?"
   Confirm that the agent continues across channels and returns the live order status rather than
   treating it as durable customer memory.

Restart the application before another rehearsal to reset the simulated order store.

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
