"""Stable Twilio wiring for the live-edited demo agent."""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from tac import TAC, TACConfig
from tac.channels.sms import SMSChannel, SMSChannelConfig
from tac.channels.voice import ConversationRelayProviderConfig, VoiceChannel
from tac.models.session import ConversationSession
from tac.models.tac import TACMemoryResponse
from tac.models.voice import VoiceTwiMLOptionsConversationRelay
from tac.server import TACFastAPIServer

from conversation_agent.agent import DemoAgent


def quiet_library_logs() -> None:
    """Keep demo output prominent while preserving warnings and errors."""

    logging.getLogger().setLevel(logging.WARNING)
    for name in ("tac", "uvicorn", "uvicorn.access", "httpx", "openai"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.WARNING)
        for handler in logger.handlers:
            handler.setLevel(logging.WARNING)


def create_server() -> TACFastAPIServer:
    """Build the configured TAC server without starting network listeners."""

    load_dotenv()
    quiet_library_logs()
    tac = TAC(config=TACConfig.from_env())
    quiet_library_logs()
    voice_channel = VoiceChannel(
        tac,
        config=ConversationRelayProviderConfig(
            memory_mode="once",
            default_twiml_options=VoiceTwiMLOptionsConversationRelay(
                welcome_greeting="Thanks for calling Owl Bakery! How can I help you?",
                voice="MzqUf1HbJ8UmQ0wUsx2p",
            ),
        ),
    )
    agent = DemoAgent(tac)

    async def handle_message_ready(
        user_message: str,
        context: ConversationSession,
        memory_response: TACMemoryResponse | None,
    ) -> str | None:
        """Stream voice responses while returning complete messaging responses."""

        if context.channel == "VOICE":
            stream = agent.stream_message(user_message, context, memory_response)
            await voice_channel.send_response(context.conversation_id, stream)
            return None

        return await agent.handle_message(user_message, context, memory_response)

    tac.on_message_ready(handle_message_ready)
    tac.on_conversation_ended(agent.end_conversation)

    app = FastAPI(
        title="Conversational Agent Memory Demo",
        description="One conversation agent shared by Twilio SMS and Voice.",
        version="0.1.0",
    )
    server = TACFastAPIServer(
        tac=tac,
        voice_channel=voice_channel,
        messaging_channels=[SMSChannel(tac, config=SMSChannelConfig(memory_mode="always"))],
        app=app,
    )

    @app.get("/health", tags=["operations"], summary="Check application health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return server


def main() -> None:
    create_server().start()


if __name__ == "__main__":
    main()
