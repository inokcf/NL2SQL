"""
会话记忆加载节点

负责在关键词抽取之前加载多轮上下文：
- 从 Redis 读取最近 N 条短期消息
- 从 Qdrant 语义检索与该问题相关的长期记忆
- 结合历史对话把追问改写成可以独立理解的问题

记忆能力属于增强项，即使 Redis 或 Qdrant 暂时不可用，也会降级为单轮问数继续执行
"""

from dataclasses import asdict

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def load_memory(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """加载短期会话和长期向量记忆，并完成问题改写"""

    writer = runtime.stream_writer
    step = "加载会话记忆"
    writer({"type": "progress", "step": step, "status": "running"})

    query = state["query"]
    session_id = state.get("session_id", "")
    user_id = state.get("user_id") or "default"

    try:
        memory_service = runtime.context["conversation_memory_service"]
        context = await memory_service.load_context(
            user_id=user_id,
            session_id=session_id,
            query=query,
        )

        history = [asdict(message) for message in context.history]
        memories = [asdict(memory) for memory in context.memories]

        logger.info(
            f"加载会话记忆：session_id={session_id}, "
            f"历史消息={len(history)}, 长期记忆={len(memories)}, "
            f"改写问题={context.resolved_query}"
        )
        writer({"type": "progress", "step": step, "status": "success"})
        return {
            "resolved_query": context.resolved_query,
            "conversation_history": history,
            "history_context": memory_service.format_history(context.history),
            "relevant_memories": memories,
            "memory_context": memory_service.format_memories(context.memories),
        }
    except Exception as e:
        # 记忆不可用不应该阻断问数主流程，降级为无历史、无长期记忆的单轮执行
        logger.warning(f"{step} 失败，将降级为单轮问数：{e}")
        writer({"type": "progress", "step": step, "status": "success"})
        return {
            "resolved_query": query,
            "conversation_history": [],
            "history_context": "无",
            "relevant_memories": [],
            "memory_context": "无",
        }
