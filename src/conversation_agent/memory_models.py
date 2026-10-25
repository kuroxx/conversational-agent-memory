"""Diagnostic models mapping recalled Twilio context to CoALA memory types.

These models provide an explanatory view; the agent uses the underlying context directly.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, Field
from tac.models.session import ConversationSession
from tac.models.tac import TACMemoryResponse


class WorkingMemory(BaseModel):
    """Context actively available to the model for the current turn."""

    conversation_id: str
    channel: str
    current_input: str
    history: list[dict[str, Any]] = Field(default_factory=list)
    assembled_instructions: str
    active_tools: list[str] = Field(default_factory=list)


class EpisodicMemory(BaseModel):
    """Recalled summaries of previous customer conversations."""

    summaries: list[dict[str, Any]] = Field(default_factory=list)


class SemanticMemory(BaseModel):
    """Recalled customer traits and observations treated as durable knowledge."""

    profile_id: str | None = None
    traits: dict[str, Any] = Field(default_factory=dict)
    observations: list[dict[str, Any]] = Field(default_factory=list)


class ProceduralMemory(BaseModel):
    """Stable agent instructions and conversation-eligible capabilities."""

    base_instructions: str
    tools: list[str] = Field(default_factory=list)


class LongTermMemory(BaseModel):
    """Long-term memory recalled or activated for the current turn."""

    episodic: EpisodicMemory
    semantic: SemanticMemory
    procedural: ProceduralMemory


class MemorySnapshot(BaseModel):
    """Diagnostic view of recalled long-term memory and current working memory."""

    long_term: LongTermMemory
    short_term: WorkingMemory


def build_memory_snapshot(
    *,
    context: ConversationSession,
    memory_response: TACMemoryResponse | None,
    current_input: str,
    history: Iterable[Any],
    assembled_instructions: str,
    base_instructions: str,
    tools: Iterable[Any],
) -> MemorySnapshot:
    """Build a diagnostic snapshot of the context available before a turn."""

    summaries = memory_response.summaries if memory_response else []
    observations = memory_response.observations if memory_response else []
    tool_names = [_tool_name(tool) for tool in tools]

    return MemorySnapshot(
        short_term=WorkingMemory(
            conversation_id=context.conversation_id,
            channel=context.channel,
            current_input=current_input,
            history=[_as_dict(item) for item in history],
            assembled_instructions=assembled_instructions,
            active_tools=tool_names,
        ),
        long_term=LongTermMemory(
            episodic=EpisodicMemory(
                summaries=[_as_dict(item) for item in summaries],
            ),
            semantic=SemanticMemory(
                profile_id=context.profile_id,
                traits=dict(context.profile.traits)
                if context.profile and context.profile.traits
                else {},
                observations=[_as_dict(item) for item in observations],
            ),
            procedural=ProceduralMemory(
                base_instructions=base_instructions,
                tools=tool_names,
            ),
        ),
    )


def _as_dict(value: Any) -> dict[str, Any]:
    """Convert SDK and Pydantic values into JSON-friendly mappings."""

    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Cannot represent {type(value).__name__} in a memory snapshot")


def _tool_name(tool: Any) -> str:
    """Return a readable name for an OpenAI Agents SDK tool."""

    name = getattr(tool, "name", None)
    if isinstance(name, str):
        return name
    return type(tool).__name__
