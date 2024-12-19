import operator
from pydantic import BaseModel, Field
from typing import Annotated, List
from typing_extensions import TypedDict

from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    get_buffer_string,
)
from langchain_openai import ChatOpenAI

from langgraph.constants import Send
from langgraph.graph import END, MessagesState, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from eenhance.utils.config import load_config

config = load_config()

# LLM

llm = ChatOpenAI(model="deepseek-chat", temperature=0)

# Schema


class Analyst(BaseModel):
    affiliation: str = Field(
        description="分析师的主要隶属机构。",
    )
    name: str = Field(description="分析师的姓名。")
    role: str = Field(
        description="分析师在该主题背景下的角色。",
    )
    description: str = Field(
        description="分析师在主题背景下的关注、关注点和动机。",
    )

    @property
    def persona(self) -> str:
        return f"姓名: {self.name}\n角色: {self.role}\n隶属关系: {self.affiliation}\n描述: {self.description}\n"


class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(
        description="分析师的全面列表，包括他们的角色和隶属关系。",
    )


class GenerateAnalystsState(TypedDict):
    topic: str  # Research topic
    max_analysts: int  # Number of analysts
    human_analyst_feedback: str  # Human feedback
    analysts: List[Analyst]  # Analyst asking questions


class InterviewState(MessagesState):
    max_num_turns: int  # Number turns of conversation
    context: Annotated[list, operator.add]  # Source docs
    analyst: Analyst  # Analyst asking questions
    interview: str  # Interview transcript
    sections: list  # Final key we duplicate in outer state for Send() API


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="检索查询。")


class ResearchGraphState(TypedDict):
    topic: str  # Research topic
    max_analysts: int  # Number of analysts
    human_analyst_feedback: str  # Human feedback
    analysts: List[Analyst]  # Analyst asking questions
    sections: Annotated[list, operator.add]  # Send() API key
    introduction: str  # Introduction for the final report
    content: str  # Content for the final report
    conclusion: str  # Conclusion for the final report
    final_report: str  # Final report


# Nodes and edges

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


def human_feedback(state: GenerateAnalystsState):
    """No-op node that should be interrupted on"""
    pass


# Generate analyst question
question_instructions = """你是一名分析师,负责采访专家以了解特定主题。

你的目标是提炼出与你主题相关的有趣且具体的见解。

1. 有趣:人们会觉得令人惊讶或不明显的见解。
2. 具体:避免泛泛而谈,包含来自专家的具体例子。
以下是你的关注主题和目标: {goals}
首先用适合你角色的名字介绍自己,然后提出你的问题。
继续提问以深入了解和完善你对主题的理解。
当你对理解感到满意时,以"非常感谢你的帮助!"结束采访。
记住在整个回答过程中保持角色特征,反映提供给你的角色和目标。"""


def generate_question(state: InterviewState):
    """Node to generate a question"""

    # Get state
    analyst = state["analyst"]
    messages = state["messages"]

    # Generate question
    system_message = question_instructions.format(goals=analyst.persona)
    question = llm.invoke([SystemMessage(content=system_message)] + messages)

    # Write messages to state
    return {"messages": [question]}


# Search query writing
search_instructions = SystemMessage(
    content="""你将获得分析师和专家之间的对话。

你的目标是生成一个结构良好的查询,用于检索和/或与对话相关的网络搜索。
首先,分析完整的对话。
特别注意分析师提出的最后一个问题。
将这个最后的问题转换为结构良好的网络搜索查询"""
)


def search_web(state: InterviewState):
    """Retrieve docs from web search"""

    # Search
    tavily_search = TavilySearchResults(max_results=3)

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + state["messages"])

    # Search
    search_docs = tavily_search.invoke(search_query.search_query)

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]}


def search_wikipedia(state: InterviewState):
    """Retrieve docs from wikipedia"""

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + state["messages"])

    # Search
    search_docs = WikipediaLoader(
        query=search_query.search_query, load_max_docs=2
    ).load()

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]}


# Generate expert answer
answer_instructions = """你是一位正在接受分析师采访的专家。

以下是分析师的关注领域: {goals}。

你的目标是回答采访者提出的问题。

要回答问题,请使用以下背景资料:

{context}

回答问题时,请遵循以下准则:

1. 仅使用背景资料中提供的信息。

2. 不要引入外部信息或对背景资料中未明确说明的内容做出假设。

3. 背景资料在每个单独文档的主题中包含来源。

4. 在你的回答中的相关陈述旁边包含这些来源。例如,对于来源#1使用[1]。

5. 在回答底部按顺序列出你的来源。[1] 来源1, [2] 来源2,等等

6. 如果来源是: <Document source="assistant/docs/llama3_1.pdf" page="7"/>,则只需列出:

[1] assistant/docs/llama3_1.pdf, 第7页

在引用时省略方括号以及Document source前缀。"""


def generate_answer(state: InterviewState):
    """Node to answer a question"""

    # Get state
    analyst = state["analyst"]
    messages = state["messages"]
    context = state["context"]

    # Answer question
    system_message = answer_instructions.format(goals=analyst.persona, context=context)
    answer = llm.invoke([SystemMessage(content=system_message)] + messages)

    # Name the message as coming from the expert
    answer.name = "expert"

    # Append it to state
    return {"messages": [answer]}


def save_interview(state: InterviewState):
    """Save interviews"""

    # Get messages
    messages = state["messages"]

    # Convert interview to a string
    interview = get_buffer_string(messages)

    # Save to interviews key
    return {"interview": interview}


def route_messages(state: InterviewState, name: str = "expert"):
    """Route between question and answer"""

    # Get messages
    messages = state["messages"]
    max_num_turns = state.get("max_num_turns", 2)

    # Check the number of expert answers
    num_responses = len(
        [m for m in messages if isinstance(m, AIMessage) and m.name == name]
    )

    # End if expert has answered more than the max turns
    if num_responses >= max_num_turns:
        return "save_interview"

    # This router is run after each question - answer pair
    # Get the last question asked to check if it signals the end of discussion
    last_question = messages[-2]

    if "非常感谢你的帮助" in last_question.content:
        return "save_interview"
    return "ask_question"


# Write a summary (section of the final report) of the interview
section_writer_instructions = """你是一位专业的技术写作者。

你的任务是根据一组源文档创建一份简短、易于理解的报告章节。

1. 分析源文档的内容:
- 每个源文档的名称都在文档开头,带有<Document标签。

2. 使用markdown格式创建报告结构:
- 使用##作为章节标题
- 使用###作为子章节标题

3. 按照此结构编写报告:
a. 标题(##标题)
b. 摘要(###标题)
c. 来源(###标题)

4. 根据分析师的关注领域制作引人入胜的标题:
{focus}

5. 对于摘要部分:
- 用与分析师关注领域相关的一般背景/上下文设置摘要
- 强调从采访中收集的新颖、有趣或令人惊讶的见解
- 创建源文档的编号列表
- 不要提及采访者或专家的姓名
- 目标最多400字
- 在报告中使用编号的来源(例如[1], [2])

6. 在来源部分:
- 包含报告中使用的所有来源
- 提供相关网站或特定文档路径的完整链接
- 用换行符分隔每个来源。在每行末尾使用两个空格以在Markdown中创建换行。
- 它看起来像:

### 来源
[1] 链接或文档名称
[2] 链接或文档名称

7. 确保合并来源。例如这是不正确的:

[3] https://ai.meta.com/blog/meta-llama-3-1/
[4] https://ai.meta.com/blog/meta-llama-3-1/

不应该有重复的来源。应该简单地是:

[3] https://ai.meta.com/blog/meta-llama-3-1/

8. 最终审查:
- 确保报告遵循所需结构
- 在报告标题之前不包含任何前言
- 检查是否遵循了所有准则"""


def write_section(state: InterviewState):
    """Node to write a section"""

    # Get state
    interview = state["interview"]
    context = state["context"]
    analyst = state["analyst"]

    # Write section using either the gathered source docs from interview (context) or the interview itself (interview)
    system_message = section_writer_instructions.format(focus=analyst.description)
    section = llm.invoke(
        [SystemMessage(content=system_message)]
        + [HumanMessage(content=f"使用这些来源撰写你的章节: {context}")]
    )

    # Append it to state
    return {"sections": [section.content]}


# Add nodes and edges
interview_builder = StateGraph(InterviewState)
interview_builder.add_node("ask_question", generate_question)
interview_builder.add_node("search_web", search_web)
interview_builder.add_node("search_wikipedia", search_wikipedia)
interview_builder.add_node("answer_question", generate_answer)
interview_builder.add_node("save_interview", save_interview)
interview_builder.add_node("write_section", write_section)

# Flow
interview_builder.add_edge(START, "ask_question")
interview_builder.add_edge("ask_question", "search_web")
interview_builder.add_edge("ask_question", "search_wikipedia")
interview_builder.add_edge("search_web", "answer_question")
interview_builder.add_edge("search_wikipedia", "answer_question")
interview_builder.add_conditional_edges(
    "answer_question", route_messages, ["ask_question", "save_interview"]
)
interview_builder.add_edge("save_interview", "write_section")
interview_builder.add_edge("write_section", END)


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
    conclusion = llm.invoke([instructions] + [HumanMessage(content=f"撰写报告结论")])
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
        except:
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
builder.add_node("create_analysts", create_analysts)
builder.add_node("human_feedback", human_feedback)
builder.add_node("conduct_interview", interview_builder.compile())
builder.add_node("write_report", write_report)
builder.add_node("write_introduction", write_introduction)
builder.add_node("write_conclusion", write_conclusion)
builder.add_node("finalize_report", finalize_report)

# Logic
builder.add_edge(START, "create_analysts")
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
graph = builder.compile(interrupt_before=["human_feedback"], checkpointer=memory)
