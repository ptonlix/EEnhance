from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import logging
from eenhance.blog.generator import ContentGenerator
from eenhance.utils.config_conversation import load_conversation_config
from pathlib import Path
from eenhance.constants import PROJECT_ROOT_PATH
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


# 研究主题助手的输入参数
class BlogInput(TypedDict):
    final_report: str  # 研究报告
    final_report_file: str  # 研究报告保存路径
    regenerate: bool  # 是否需要重新生成文案


class BlogOutput(TypedDict):
    blog_content: str  # 博客内容
    blog_file_path: str  # 博客保存路径
    error: str | None


def human_feedback(state: BlogInput):
    pass


def generate_blog(state: BlogInput) -> BlogOutput:
    try:
        conv_config = load_conversation_config()
        config_conversation = conv_config.to_dict()

        content_generator = ContentGenerator(
            model_name="glm-4-plus",
            conversation_config=config_conversation,
        )

        if state.get("final_report"):
            final_report = state["final_report"]
        else:
            # 读取研究报告内容
            with open(state["final_report_file"], "r") as file:
                final_report = file.read()

        print(final_report)
        file_name = Path(state["final_report_file"]).stem + "_blog.txt"
        filepath = Path(PROJECT_ROOT_PATH) / "data" / "transcripts" / file_name
        qa_content = content_generator.generate_qa_content(
            final_report,
            image_file_paths=[],
            output_filepath=filepath,
            longform=True,
        )

        return BlogOutput(blog_content=qa_content, blog_file_path=filepath, error=None)
    except Exception as e:
        logger.error(f"生成博客内容时发生错误: {str(e)}")
        return BlogOutput(blog_content="", blog_file_path="", error=str(e))


def router(state: BlogInput):
    if state.get("regenerate"):
        return "generate"
    else:
        return "end"


# 创建状态图
graph = StateGraph(input=BlogInput, output=BlogOutput)

# 添加节点
graph.add_node("human_feedback", human_feedback)
graph.add_node("generate", generate_blog)

# 添加边
graph.add_edge(START, "human_feedback")
graph.add_conditional_edges(
    "human_feedback", router, {"generate": "generate", "end": END}
)
graph.add_edge("generate", "human_feedback")

# 添加检查点
memory = MemorySaver()
graph = graph.compile(interrupt_before=["human_feedback"], checkpointer=memory)
