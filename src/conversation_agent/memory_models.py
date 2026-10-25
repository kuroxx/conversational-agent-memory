"""CoALA memory types and context assembly used in the demo."""

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, Field
from tac.models.session import ConversationSession
from tac.models.tac import TACMemoryResponse


class WorkingMemory(BaseModel):
    """Recent messages from the active agent session."""

    conversation_id: str
    channel: str
    history: list[dict[str, Any]] = Field(default_factory=list)


class EpisodicMemory(BaseModel):
    """Previous customer interactions and conversation summaries."""

    summaries: list[dict[str, Any]] = Field(default_factory=list)
    communications: list[dict[str, Any]] = Field(default_factory=list)


class SemanticMemory(BaseModel):
    """Known customer facts, preferences, and observations."""

    profile_id: str | None = None
    traits: dict[str, Any] = Field(default_factory=dict)
    observations: list[dict[str, Any]] = Field(default_factory=list)


class ProceduralMemory(BaseModel):
    """Instructions and tools that define what the agent can do."""

    instructions: str
    tools: list[str] = Field(default_factory=list)


class MemoryContext(BaseModel):
    """The four memory types shown during the demo."""

    working: WorkingMemory
    episodic: EpisodicMemory
    semantic: SemanticMemory
    procedural: ProceduralMemory


def build_memory_context(
    *,
    context: ConversationSession,
    memory_response: TACMemoryResponse | None,
    history: Iterable[Any],
    instructions: str,
    tools: Iterable[Any],
) -> MemoryContext:
    """Build a display snapshot without creating a second memory store."""

    summaries = memory_response.summaries if memory_response else []
    communications = memory_response.communications if memory_response else []
    observations = memory_response.observations if memory_response else []

    return MemoryContext(
        working=WorkingMemory(
            conversation_id=context.conversation_id,
            channel=context.channel,
            history=[_as_dict(item) for item in history],
        ),
        episodic=EpisodicMemory(
            summaries=[_as_dict(item) for item in summaries],
            communications=[_as_dict(item) for item in communications],
        ),
        semantic=SemanticMemory(
            profile_id=context.profile_id,
            traits=dict(context.profile.traits)
            if context.profile and context.profile.traits
            else {},
            observations=[_as_dict(item) for item in observations],
        ),
        procedural=ProceduralMemory(
            instructions=instructions,
            tools=[_tool_name(tool) for tool in tools],
        ),
    )


def _as_dict(value: Any) -> dict[str, Any]:
    """Convert SDK and Pydantic values into JSON-friendly mappings."""

    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Cannot represent {type(value).__name__} in a memory context")


def _tool_name(tool: Any) -> str:
    """Return a readable name for an OpenAI Agents SDK tool."""

    name = getattr(tool, "name", None)
    if isinstance(name, str):
        return name
    return type(tool).__name__
