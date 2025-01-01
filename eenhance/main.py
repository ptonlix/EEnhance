from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict

from eenhance.content.content_assistant import graph as content_graph
from eenhance.topic.topic_assistant import graph as topic_graph
from eenhance.research.research_assistant import graph as research_graph
from eenhance.blog.blog_assistant import graph as blog_graph
from eenhance.tts.tts_assistant import graph as tts_graph


# 定义整体流程的状态
from eenhance.content.content_assistant import ContentInput, ContentOutput
from eenhance.topic.topic_assistant import TopicInput, TopicOutput
from eenhance.research.schemas import ResearchGraphState
from eenhance.blog.blog_assistant import BlogInput, BlogOutput
from eenhance.tts.tts_assistant import TTSInput, TTSOutput


class EenhanceState(
    TypedDict,
    ContentInput,
    ContentOutput,
    TopicInput,
    TopicOutput,
    ResearchGraphState,
    BlogInput,
    BlogOutput,
    TTSInput,
    TTSOutput,
):
    """整合多个TypedDict类的状态"""

    error: str | None


# 创建工作流图
workflow = StateGraph(EenhanceState)

# 添加节点
workflow.add_node("content_agent", content_graph)
workflow.add_node("topic_agent", topic_graph)
workflow.add_node("research_agent", research_graph)
workflow.add_node("blog_agent", blog_graph)
workflow.add_node("tts_agent", tts_graph)

# 添加边
workflow.add_edge(START, "content_agent")
workflow.add_edge("content_agent", "topic_agent")
workflow.add_edge("topic_agent", "research_agent")
workflow.add_edge("research_agent", "blog_agent")
workflow.add_edge("blog_agent", "tts_agent")
workflow.add_edge("tts_agent", END)

# 编译图
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    # 生成图片并保存到文件
    graph_image = graph.get_graph(xray=1).draw_mermaid_png()
    with open("workflow_graph.png", "wb") as f:
        f.write(graph_image)
