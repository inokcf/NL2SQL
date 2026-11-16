"""
长期会话记忆业务实体

长期记忆保存到 Qdrant，一条记忆对应一个向量点
episodic 表示一轮问数记录，semantic 表示从对话中抽取出的稳定偏好或业务口径
"""

from dataclasses import dataclass


@dataclass
class ConversationMemory:
    """可被语义检索的长期记忆"""

    id: str
    user_id: str
    session_id: str
    # episodic：历史问数记录；semantic：用户偏好 术语映射 口径约束
    memory_type: str
    # 真正参与 Embedding 的文本
    content: str
    question: str = ""
    resolved_query: str = ""
    sql: str = ""
    created_at: str = ""
    # 检索时由 Qdrant 回填，不写入 payload
    score: float | None = None
