"""
生成研究主题助手
"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import logging
from langchain.prompts import PromptTemplate
from eenhance.utils.llm import llm_factory
from langchain.output_parsers import CommaSeparatedListOutputParser

logger = logging.getLogger(__name__)


# 研究主题助手的输入参数
class TopicInput(TypedDict):
    out_content: str  # 主要输入的内容
    additional_info: str | None  # 用户提供的额外信息
    selected_topic: str | None  # 用户选择的主题
    regenerate: bool  # 是否需要重新生成主题


# 研究主题助手的输出参数
class TopicOutput(TypedDict):
    topics: list[str]  # 生成的研究主题列表
    selected_topic: str | None  # 最终选定的主题
    error: str | None


def human_feedback(state: TopicInput):
    pass


def generate_topics(state: TopicInput) -> TopicOutput:
    try:

        # 创建输出解析器
        output_parser = CommaSeparatedListOutputParser()

        # 定义提示模板
        template = """基于以下内容和补充信息，生成3个具体且有深度的研究主题：

主要内容：{content}

{additional_info_prompt}

要求：
1. 每个主题应该明确且具有研究价值
2. 主题应该相互独立，覆盖不同的研究角度
3. 确保主题与输入内容密切相关
4. 考虑补充信息提供的具体要求或限制

请生成3个研究主题，用逗号分隔。
"""

        # 处理额外信息
        additional_info = state.get("additional_info")
        additional_info_prompt = (
            f"补充信息：{additional_info}" if additional_info else "补充信息：无"
        )

        # 创建prompt
        prompt = PromptTemplate(
            template=template,
            input_variables=["content", "additional_info_prompt"],
            output_parser=output_parser,
        )

        # 初始化LLM
        llm = llm_factory.create_llm(use_case="topic", temperature=0.7)

        # 生成主题
        _input = prompt.format(
            content=state["out_content"], additional_info_prompt=additional_info_prompt
        )
        topics = llm.invoke(_input)
        topics = output_parser.parse(topics.content)

        return TopicOutput(
            topics=topics[:3],  # 确保只返回3个主题
            selected_topic=state.get("selected_topic"),
            error=None,
        )
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        return TopicOutput(topics=[], selected_topic=None, error=str(e))


def router(state: TopicInput):
    if state.get("selected_topic"):
        return "end"
    elif state.get("regenerate"):
        return "generate"
    else:
        return "end"


# 创建状态图
graph = StateGraph(input=TopicInput, output=TopicOutput)

# 添加节点
graph.add_node("human_feedback", human_feedback)
graph.add_node("generate", generate_topics)

# 添加边
graph.add_edge(START, "human_feedback")
graph.add_conditional_edges(
    "human_feedback", router, {"generate": "generate", "end": END}
)
graph.add_edge("generate", "human_feedback")

# 添加检查点
memory = MemorySaver()
graph = graph.compile(interrupt_before=["human_feedback"], checkpointer=memory)
