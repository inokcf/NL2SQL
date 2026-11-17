"""
分析结论生成节点

负责在 SQL 执行成功后，把结构化查询结果转换成面向业务用户的自然语言回答
节点会结合用户问题、改写后的问题、指标口径和结果数据生成结论，并以 SSE
answer 事件返回给前端；生成失败时回退到确定性的结果摘要，保证流程不中断
"""

import json

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.prompt.prompt_loader import load_prompt

# 传给模型的结果预览行数，避免大结果集撑爆提示词
MAX_PREVIEW_ROWS = 20


def _fallback_answer(rows: list[dict]) -> str:
    """模型不可用时的确定性兜底回答"""
    if not rows:
        return "查询已完成，但没有找到符合条件的数据。"
    if len(rows) == 1 and isinstance(rows[0], dict):
        values = "，".join(f"{key}：{value}" for key, value in rows[0].items())
        return f"查询结果为：{values}。"
    return f"查询完成，共返回 {len(rows)} 行结果。"


def _clean_answer(answer: str) -> str:
    """清理模型偶尔带出的前缀和代码块符号"""
    answer = (answer or "").strip()
    if answer.startswith("```"):
        answer = answer.strip("`").strip()
    for prefix in ("回答：", "分析结论：", "结论："):
        if answer.startswith(prefix):
            answer = answer[len(prefix) :].strip()
    return answer[:2000]


async def generate_answer(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """把 SQL 结果转换为自然语言业务结论"""

    writer = runtime.stream_writer
    step = "生成分析结论"
    writer({"type": "progress", "step": step, "status": "running"})

    rows: list[dict] = state.get("sql_result") or []
    answer = ""

    try:
        query = state["query"]
        resolved_query = state.get("resolved_query") or query
        sql = state.get("sql") or ""
        metric_infos = state.get("metric_infos") or []

        result_preview = json.dumps(
            rows[:MAX_PREVIEW_ROWS],
            ensure_ascii=False,
            default=str,
            indent=2,
        )[:6000]

        prompt = PromptTemplate(
            template=load_prompt("generate_answer"),
            input_variables=[
                "query",
                "resolved_query",
                "metric_infos",
                "sql",
                "row_count",
                "result_preview",
            ],
        )
        chain = prompt | llm | StrOutputParser()
        answer = await chain.ainvoke(
            {
                "query": query,
                "resolved_query": resolved_query,
                "metric_infos": yaml.dump(
                    metric_infos, allow_unicode=True, sort_keys=False
                ),
                "sql": sql,
                "row_count": len(rows),
                "result_preview": result_preview,
            }
        )
        answer = _clean_answer(answer)
    except Exception as e:
        # 结论生成失败不影响已经拿到的查询结果，使用确定性摘要兜底
        logger.warning(f"{step} failed，将使用兜底结论：{e}")

    if not answer:
        answer = _fallback_answer(rows)

    logger.info(f"分析结论：{answer}")
    writer({"type": "progress", "step": step, "status": "success"})
    writer({"type": "answer", "content": answer})
    return {"answer": answer}
