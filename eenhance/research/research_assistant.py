from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from .schemas import GenerateAnalystsState, ResearchGraphState, Perspectives
from .interview_assistant import interview_builder
from eenhance.utils.llm import llm_factory
import logging

logger = logging.getLogger(__name__)

llm = llm_factory.create_llm(use_case="research", temperature=0)

# 分析师创建指令
analyst_instructions = """你的任务是创建一组AI分析师角色。请仔细遵循以下说明:

1. 首先,审查研究主题:
{topic}

2. 检查所提供的任何可选的编辑反馈,以指导分析师的创建:

{human_analyst_feedback}

3. 根据上述文档和/或反馈确定最有趣的主题。

4. 选择前{max_analysts}个主题。

5. 为每个主题分配一名分析师。"""


def create_analysts(state: GenerateAnalystsState):
    """Create analysts"""
    logger.error(f"Creating analysts with state: {state}")
    topic = state["topic"]
    max_analysts = state["max_analysts"]
    human_analyst_feedback = state.get("human_analyst_feedback", "")

    # Enforce structured output
    structured_llm = llm.with_structured_output(Perspectives)

    # System message
    system_message = analyst_instructions.format(
        topic=topic,
        human_analyst_feedback=human_analyst_feedback,
        max_analysts=max_analysts,
    )

    # Generate question
    analysts = structured_llm.invoke(
        [SystemMessage(content=system_message)]
        + [HumanMessage(content="生成分析师集合。")]
    )

    # Write the list of analysis to state
    return {"analysts": analysts.analysts}


def human_input(state: GenerateAnalystsState):
    """No-op node that should be interrupted on"""
    pass


def human_feedback(state: GenerateAnalystsState):
    """No-op node that should be interrupted on"""
    pass


def initiate_all_interviews(state: ResearchGraphState):
    """Conditional edge to initiate all interviews via Send() API or return to create_analysts"""

    # Check if human feedback
    human_analyst_feedback = state.get("human_analyst_feedback", "approve")
    if human_analyst_feedback.lower() != "approve":
        # Return to create_analysts
        return "create_analysts"

    # Otherwise kick off interviews in parallel via Send() API
    else:
        topic = state["topic"]
        return [
            Send(
                "conduct_interview",
                {
                    "analyst": analyst,
                    "messages": [
                        HumanMessage(content=f"你正在写一篇关于{topic}的文章吗?")
                    ],
                },
            )
            for analyst in state["analysts"]
        ]


# Write a report based on the interviews
report_writer_instructions = """你是一位技术写作者,正在撰写关于以下总体主题的报告:

{topic}

你有一个分析师团队。每个分析师做了两件事:

1. 他们就特定子主题采访了一位专家。
2. 他们将调查结果写成备忘录。

你的任务:

1. 你将获得来自分析师的一系列备忘录。
2. 仔细思考每份备忘录中的见解。
3. 将这些见解整合成一个简明的总体摘要,将所有备忘录中的核心思想联系在一起。
4. 将每份备忘录中的核心要点总结成一个连贯的单一叙述。

报告格式要求:

1. 使用markdown格式。
2. 不包含报告前言。
3. 不使用子标题。
4. 用单一标题标题开始你的报告:## 见解
5. 不要在报告中提及任何分析师姓名。
6. 保留备忘录中的任何引用,这些引用将用方括号标注,例如[1]或[2]。
7. 创建一个最终的综合来源列表,并添加到带有`## 来源`标题的来源部分。
8. 按顺序列出你的来源,不要重复。

[1] 来源1
[2] 来源2

以下是你的分析师的备忘录,用于构建你的报告:

{context}"""


def write_report(state: ResearchGraphState):
    """Node to write the final report body"""

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

    # Summarize the sections into a final report
    system_message = report_writer_instructions.format(
        topic=topic, context=formatted_str_sections
    )
    report = llm.invoke(
        [SystemMessage(content=system_message)]
        + [HumanMessage(content="撰写基于这些备忘录的报告")]
    )
    return {"content": report.content}


# Write the introduction or conclusion
intro_conclusion_instructions = """你是一位正在完成关于{topic}的报告的技术写作者。

你将获得报告的所有章节。

你的工作是写一个简明有力的引言或结论部分。

用户会指示你写引言还是结论。

两个部分都不要包含前言。

目标大约100字,简明扼要地预览(引言)或回顾(结论)报告的所有章节。

使用markdown格式。

对于引言,创建一个引人入胜的标题并使用#标题。

对于引言,使用## 引言作为章节标题。

对于结论,使用## 结论作为章节标题。

以下是用于写作的章节: {formatted_str_sections}"""


def write_introduction(state: ResearchGraphState):
    """Node to write the introduction"""

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

    # Summarize the sections into a final report

    instructions = intro_conclusion_instructions.format(
        topic=topic, formatted_str_sections=formatted_str_sections
    )
    intro = llm.invoke([instructions] + [HumanMessage(content="撰写报告引言")])
    return {"introduction": intro.content}


def write_conclusion(state: ResearchGraphState):
    """Node to write the conclusion"""

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])

    # Summarize the sections into a final report

    instructions = intro_conclusion_instructions.format(
        topic=topic, formatted_str_sections=formatted_str_sections
    )
    conclusion = llm.invoke([instructions] + [HumanMessage(content="撰写报告结论")])
    return {"conclusion": conclusion.content}


def finalize_report(state: ResearchGraphState):
    """The is the "reduce" step where we gather all the sections, combine them, and reflect on them to write the intro/conclusion"""

    # Save full final report
    content = state["content"]
    if content.startswith("## 见解"):
        content = content.strip("## 见解")
    if "## 来源" in content:
        try:
            content, sources = content.split("\n## 来源\n")
        except Exception:
            sources = None
    else:
        sources = None

    final_report = (
        state["introduction"]
        + "\n\n---\n\n"
        + content
        + "\n\n---\n\n"
        + state["conclusion"]
    )
    if sources is not None:
        final_report += "\n\n## 来源\n" + sources
    return {"final_report": final_report}


# Add nodes and edges
builder = StateGraph(ResearchGraphState)
builder.add_node("human_input", human_input)
builder.add_node("create_analysts", create_analysts)
builder.add_node("human_feedback", human_feedback)
builder.add_node("conduct_interview", interview_builder.compile())
builder.add_node("write_report", write_report)
builder.add_node("write_introduction", write_introduction)
builder.add_node("write_conclusion", write_conclusion)
builder.add_node("finalize_report", finalize_report)

# Logic
builder.add_edge(START, "human_input")
builder.add_edge("human_input", "create_analysts")
builder.add_edge("create_analysts", "human_feedback")
builder.add_conditional_edges(
    "human_feedback", initiate_all_interviews, ["create_analysts", "conduct_interview"]
)
builder.add_edge("conduct_interview", "write_report")
builder.add_edge("conduct_interview", "write_introduction")
builder.add_edge("conduct_interview", "write_conclusion")
builder.add_edge(
    ["write_conclusion", "write_report", "write_introduction"], "finalize_report"
)
builder.add_edge("finalize_report", END)

# Compile
memory = MemorySaver()
graph = builder.compile(
    interrupt_before=["human_input", "human_feedback"], checkpointer=memory
)
