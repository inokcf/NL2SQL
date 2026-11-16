"""
会话消息业务实体

短期会话记忆以消息列表形式保存在 Redis 中，用户问题和助手回复都使用同一结构
除展示文本外，还保留改写后问题 生成的 SQL 和附加元数据，方便下一轮追问时复用
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """一轮会话中的一条消息"""

    id: str
    # user 表示用户问题，assistant 表示系统执行结果
    role: str
    content: str
    created_at: str
    # 本轮实际执行的 SQL，便于后续追问时理解上一轮分析口径
    sql: str = ""
    # 结合历史对话补全指代后的独立问题
    resolved_query: str = ""
    # 结果行数等轻量元数据，不保存完整查询结果，避免 Redis 和提示词膨胀
    metadata: dict[str, Any] = field(default_factory=dict)
