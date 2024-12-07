from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .content_parser.content_extractor import ContentExtractor
import logging

logger = logging.getLogger(__name__)


# Content Agent 的输入参数
class ContentInput(TypedDict):
    source: str  # URL或文件路径
    content_is_open: bool


# Content Agent 的输出参数
class ContentOutput(TypedDict):
    content: str
    error: str | None


# no-op node that should be interrupted on
def human_feedback(state: ContentInput):
    print(state)


def extract_content(state: ContentInput) -> ContentOutput:
    try:
        extractor = ContentExtractor()
        content = extractor.extract_content(state["source"])
        return ContentOutput(content=content, error=None)
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return ContentOutput(content="", error=str(e))


def router(state: ContentInput):
    if state.get("content_is_open"):
        return "extract"
    else:
        return "end"


# 创建状态图
graph = StateGraph(input=ContentInput, output=ContentOutput)

# 添加节点
graph.add_node("human_feedback", human_feedback)
graph.add_node("extract", extract_content)

# 添加边
graph.add_edge(START, "human_feedback")
graph.add_conditional_edges(
    "human_feedback", router, {"extract": "extract", "end": END}
)
graph.add_edge("extract", "human_feedback")

# 添加检查点
memory = MemorySaver()
graph = graph.compile(interrupt_before=["human_feedback"], checkpointer=memory)
