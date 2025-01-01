from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    get_buffer_string,
)
from langgraph.graph import END, START, StateGraph
from .schemas import InterviewState, SearchQuery
from eenhance.utils.config import load_config
from eenhance.utils.llm import llm_factory

config = load_config()

# LLM

llm = llm_factory.create_llm(use_case="research", temperature=0)

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

    try:
        # Search
        search_docs = tavily_search.invoke(search_query.search_query)

        # 检查搜索结果是否为空
        if not search_docs:
            return {"context": ["未找到相关搜索结果"]}

        # Format
        formatted_search_docs = "\n\n---\n\n".join(
            [
                f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
                for doc in search_docs
            ]
        )

        return {"context": [formatted_search_docs]}

    except Exception as e:
        # 捕获所有可能的异常
        return {"context": [f"搜索过程中出现错误: {str(e)}"]}


def search_wikipedia(state: InterviewState):
    """Retrieve docs from wikipedia"""

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions] + state["messages"])

    try:
        # Search
        search_docs = WikipediaLoader(
            query=search_query.search_query, load_max_docs=2
        ).load()

        # 检查搜索结果是否为空
        if not search_docs:
            return {"context": ["未在维基百科中找到相关结果"]}

        # Format
        formatted_search_docs = "\n\n---\n\n".join(
            [
                f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
                for doc in search_docs
            ]
        )

        return {"context": [formatted_search_docs]}

    except Exception as e:
        # 捕获所有可能的异常
        return {"context": [f"维基百科搜索过程中出现错误: {str(e)}"]}


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
