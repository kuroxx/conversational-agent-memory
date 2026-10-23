"""Enterprise Knowledge retrieval tool for the bakery agent."""

import json
from typing import Any

from agents import FunctionTool
from tac import TAC
from tac.tools import TACTool, create_knowledge_tool


def _serialize_tool_result(value: Any) -> Any:
    """Convert Pydantic tool results into values accepted by json.dumps."""

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _to_json_agents_tool(tool: TACTool) -> FunctionTool:
    """Convert a TAC tool while supporting Pydantic response models."""

    async def on_invoke(_context: Any, arguments_json: str) -> str:
        arguments = json.loads(arguments_json) if arguments_json else {}
        result = await tool(**arguments)
        return json.dumps(result, default=_serialize_tool_result)

    return FunctionTool(
        name=tool.name,
        description=tool.description,
        params_json_schema=tool.params_json_schema,
        on_invoke_tool=on_invoke,
        strict_json_schema=False,
    )


async def create_bakery_knowledge_tool(tac: TAC) -> FunctionTool | None:
    """Create a knowledge tool when Enterprise Knowledge is configured."""

    knowledge_client = tac.knowledge_client
    knowledge_base_id = tac.config.knowledge_base_id
    if knowledge_client is None or not knowledge_base_id:
        return None

    knowledge_tool = await create_knowledge_tool(
        knowledge_client,
        knowledge_base_id,
        name="search_bakery_knowledge",
        description="Search bakery products, ingredients, allergens, and policies.",
        top_k=3,
    )
    return _to_json_agents_tool(knowledge_tool)
