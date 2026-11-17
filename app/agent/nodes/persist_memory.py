"""
会话记忆持久化节点

负责在 SQL 执行完成后把本轮问答写回记忆系统：
- Redis 保存最近 N 条短期消息，并刷新 TTL
- Qdrant 保存问数记录和抽取出的长期偏好，供后续语义检索

该节点不输出 SSE 进度，因为查询结果已经先一步返回前端，避免前端在结果之后
再次收到进度事件而覆盖已展示内容；保存失败也只记录日志，不影响本次查询结果
"""

from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def persist_memory(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """保存本轮短期会话和长期向量记忆"""

    try:
        memory_service = runtime.context["conversation_memory_service"]
        await memory_service.save_turn(
            user_id=state.get("user_id") or "default",
            session_id=state.get("session_id", ""),
            query=state["query"],
            resolved_query=state.get("resolved_query") or state["query"],
            sql=state.get("sql", ""),
            sql_result=state.get("sql_result") or [],
            answer=state.get("answer") or "",
            history=state.get("conversation_history") or [],
        )
    except Exception as e:
        logger.warning(f"保存会话记忆失败：{e}")

    # 记忆保存只产生副作用，不需要再合并任何状态字段
    return {}
