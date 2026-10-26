"""Bakery agent with cross-channel memory and action tools."""

from collections.abc import AsyncGenerator

from agents import (
    Agent,
    ModelSettings,
    RawResponsesStreamEvent,
    Runner,
    SQLiteSession,
    set_tracing_disabled,
)
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent
from tac import TAC
from tac.adapters import MemoryPromptBuilder
from tac.models.session import ConversationSession
from tac.models.tac import TACMemoryResponse

from conversation_agent.logging import log_demo
from conversation_agent.memory_models import build_memory_snapshot
from conversation_agent.tools import ToolProvider

set_tracing_disabled(True)  # ZDR blocks hosted trace ingestion.


INSTRUCTIONS = """You are Owl Bakery's friendly, efficient customer service agent.

Help customers with:
- Looking up existing orders
- Placing new bakery orders
- Changing order fulfillment details or cake inscriptions
- Checking live order and delivery status
- Answering questions about products, ingredients, allergens, delivery, pickup, and bakery policies
- Sending SMS confirmations when requested

Guidelines:
- Greet the customer by first name in your first reply on each channel once. After that, use their name sparingly.
- The customer may switch between SMS and Voice during a conversation. Treat prior turns from another channel as part of the same conversation and continue without repeating information already covered.
- Do not use markdown formatting — plain text only, since responses are sent via SMS and Voice.
- Answer only what the customer asked. 
- Keep responses concise, direct, warm, and conversational.
- For Voice, use short sentences that sound natural when spoken. Read order numbers digit by digit.
- Ask only one clarifying question at a time.
- When memories conflict, use the most recent verified information.
- Use recall_customer_memory when relevant details from earlier conversations are needed. Do not treat temporary statements as durable customer facts.
- Use lookup_orders or lookup_order for current order and cake details.
- Use get_order_status for live fulfillment status. Never rely on memory for current order status, delivery progress, or ETA.
- Use search_bakery_knowledge for product, ingredient, allergen, delivery, pickup, and policy questions.
- Never infer that a product is safe for an allergy. Explain the bakery's allergen policy and advise customers with allergies to speak with bakery staff.
- Never claim an order was placed unless create_order succeeded.
- Never claim an order changed unless update_order succeeded.
- Only send an SMS when the customer explicitly requests it. Never claim it was sent unless send_sms succeeded.
- Never make up information. Check the appropriate tool before answering.
- If a tool fails, explain the problem briefly and give the customer the next useful step.
- If the customer seems frustrated, acknowledge their feelings briefly before helping resolve the issue."""


class DemoAgent:
    def __init__(self, tac: TAC) -> None:
        self.sessions: dict[str, SQLiteSession] = {}
        self.tools = ToolProvider(tac)

    async def _prepare_turn(
        self,
        user_message: str,
        context: ConversationSession,
        memory_response: TACMemoryResponse | None,
    ) -> tuple[Agent, SQLiteSession]:
        """Build the turn-specific agent and retrieve its working-memory session."""

        instructions = MemoryPromptBuilder.compose(
            INSTRUCTIONS,
            memory_response,
            context,
        )
        log_demo("INSTRUCTIONS", instructions)

        tools = await self.tools.for_session(context)
        agent = Agent(
            name="Bakery agent",
            model="gpt-5-nano",
            model_settings=ModelSettings(
                store=False,  # Keep Responses stateless for ZDR.
                verbosity="low",
                reasoning={"effort": "minimal"},
                max_tokens=200,
            ),
            instructions=instructions,
            tools=tools,
        )
        conversation_id = context.conversation_id
        session = self.sessions.get(conversation_id)
        if session is None:
            session = SQLiteSession(conversation_id, ":memory:")
            self.sessions[conversation_id] = session

        _memory_snapshot = build_memory_snapshot(
            context=context,
            memory_response=memory_response,
            current_input=user_message,
            history=await session.get_items(),
            assembled_instructions=instructions,
            base_instructions=INSTRUCTIONS,
            tools=tools,
        )
        log_demo(f"USER INPUT [{context.channel}]", user_message)
        # log_demo("MEMORY SNAPSHOT", _memory_snapshot)
        return agent, session

    async def handle_message(
        self,
        user_message: str,
        context: ConversationSession,
        memory_response: TACMemoryResponse | None,
    ) -> str:
        """Return a complete response for messaging channels."""

        agent, session = await self._prepare_turn(user_message, context, memory_response)

        result = await Runner.run(agent, user_message, session=session)
        reply = result.final_output or "Sorry, I couldn't complete that request."
        log_demo("AI REPLY", reply)
        return reply

    async def stream_message(
        self,
        user_message: str,
        context: ConversationSession,
        memory_response: TACMemoryResponse | None,
    ) -> AsyncGenerator[str, None]:
        """Yield voice-response text as the model generates it."""

        agent, session = await self._prepare_turn(user_message, context, memory_response)
        result = Runner.run_streamed(agent, user_message, session=session)
        chunks: list[str] = []

        async for event in result.stream_events():
            if isinstance(event, RawResponsesStreamEvent) and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                delta = event.data.delta
                if delta:
                    chunks.append(delta)
                    yield delta

        reply = result.final_output or "".join(chunks)
        if not reply:
            reply = "Sorry, I couldn't complete that request."
            yield reply
        log_demo("AI REPLY", reply)

    async def end_conversation(self, context: ConversationSession) -> None:
        session = self.sessions.pop(context.conversation_id, None)
        if session:
            await session.clear_session()
